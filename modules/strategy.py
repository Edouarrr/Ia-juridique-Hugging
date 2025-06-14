"""Module de stratégie juridique avec IA - Version améliorée avec multi-modèles"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import time
import random
from pathlib import Path
import sys

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import truncate_text, clean_key, format_legal_date

logger = logging.getLogger(__name__)

def run():
    """Fonction principale du module - Point d'entrée pour le lazy loading"""
    # Initialisation de l'état du module
    if 'strategy_state' not in st.session_state:
        st.session_state.strategy_state = {
            'initialized': True,
            'current_strategy': None,
            'strategy_history': [],
            'ai_models_config': {
                'selected_models': ['claude-3'],
                'fusion_mode': False,
                'weights': {'claude-3': 0.4, 'gpt-4': 0.3, 'mistral': 0.3}
            },
            'generation_in_progress': False,
            'comparison_mode': False,
            'selected_strategies': []
        }
    
    # Animation d'entrée
    if not st.session_state.get('strategy_intro_shown', False):
        with st.container():
            cols = st.columns([1, 2, 1])
            with cols[1]:
                st.markdown(
                    """
                    <div style="text-align: center; padding: 20px;">
                        <h1 style="color: #2E86AB;">⚖️ Stratégie Juridique IA</h1>
                        <p style="color: #666; font-size: 1.2em;">
                            Développez des stratégies de défense intelligentes avec l'aide de l'IA
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        st.session_state.strategy_intro_shown = True
    
    # Interface principale avec tabs élégants
    tab_names = [
        "🎯 Nouvelle stratégie",
        "🤖 Modèles IA",
        "📚 Bibliothèque",
        "🔄 Comparaison",
        "📊 Analytics",
        "❓ Aide"
    ]
    
    tabs = st.tabs(tab_names)
    
    with tabs[0]:  # Nouvelle stratégie
        render_new_strategy()
    
    with tabs[1]:  # Configuration IA
        render_ai_config()
    
    with tabs[2]:  # Bibliothèque
        render_strategy_library()
    
    with tabs[3]:  # Comparaison
        render_strategy_comparison()
    
    with tabs[4]:  # Analytics
        render_analytics()
    
    with tabs[5]:  # Aide
        render_help()

def render_new_strategy():
    """Interface de création de stratégie avec design amélioré"""
    
    # Header avec gradient
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">🎯 Créer une nouvelle stratégie</h3>
            <p style="color: #f0f0f0; margin: 5px 0 0 0;">
                Construisez une défense sur mesure avec l'intelligence artificielle
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Templates de stratégies
    strategy_templates = get_strategy_templates()
    
    # Section 1: Configuration de base avec cards
    with st.container():
        st.markdown("### 📋 Configuration de base")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            case_type = st.selectbox(
                "Type d'affaire",
                list(strategy_templates.keys()),
                format_func=lambda x: f"{strategy_templates[x]['icon']} {strategy_templates[x]['name']}",
                help="Sélectionnez le type de contentieux"
            )
        
        with col2:
            urgency = st.select_slider(
                "⏰ Urgence",
                ["🟢 Faible", "🟡 Modérée", "🟠 Élevée", "🔴 Critique"],
                value="🟡 Modérée",
                help="Niveau d'urgence de l'affaire"
            )
        
        with col3:
            complexity = st.select_slider(
                "🧩 Complexité",
                ["🟢 Simple", "🟡 Modérée", "🟠 Complexe", "🔴 Très complexe"],
                value="🟡 Modérée",
                help="Complexité juridique et factuelle"
            )
        
        with col4:
            budget = st.selectbox(
                "💰 Budget",
                ["💵 Limité", "💵💵 Standard", "💵💵💵 Confortable", "💵💵💵💵 Illimité"],
                index=1,
                help="Budget disponible pour la défense"
            )
    
    # Section 2: Contexte avec design moderne
    st.markdown("### 📄 Contexte de l'affaire")
    
    # Zone de texte enrichie
    context = st.text_area(
        "Description détaillée",
        placeholder="""Décrivez l'affaire en incluant :
• Les faits marquants et leur chronologie
• Les parties impliquées et leurs rôles
• Les enjeux juridiques et financiers
• Les éléments de preuve disponibles
• Les objectifs prioritaires du client""",
        height=200,
        help="Plus votre description est détaillée, plus la stratégie sera pertinente"
    )
    
    # Section 3: Analyse SWOT interactive
    st.markdown("### 🎯 Analyse stratégique")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("💪 **Forces** - Atouts de votre position", expanded=True):
            strengths = st.text_area(
                "Points forts",
                placeholder="""• Preuves matérielles solides
• Témoignages favorables
• Jurisprudence applicable
• Bonne foi évidente
• Documentation complète""",
                height=120,
                label_visibility="collapsed"
            )
    
    with col2:
        with st.expander("⚠️ **Faiblesses** - Points d'attention", expanded=True):
            weaknesses = st.text_area(
                "Points faibles",
                placeholder="""• Éléments contradictoires
• Témoins peu fiables
• Délais dépassés
• Preuves manquantes
• Précédents défavorables""",
                height=120,
                label_visibility="collapsed"
            )
    
    col3, col4 = st.columns(2)
    
    with col3:
        with st.expander("🎯 **Opportunités** - Leviers favorables"):
            opportunities = st.text_area(
                "Opportunités",
                placeholder="""• Évolution jurisprudentielle récente
• Erreurs procédurales adverses
• Possibilité de négociation
• Médiation envisageable
• Opinion publique favorable""",
                height=120,
                label_visibility="collapsed"
            )
    
    with col4:
        with st.expander("🚨 **Menaces** - Risques identifiés"):
            threats = st.text_area(
                "Menaces",
                placeholder="""• Arguments adverses forts
• Jurisprudence défavorable
• Risque médiatique
• Coûts élevés
• Délais serrés""",
                height=120,
                label_visibility="collapsed"
            )
    
    # Section 4: Objectifs avec pills
    st.markdown("### 🎯 Objectifs prioritaires")
    
    objectives = st.multiselect(
        "Sélectionnez vos objectifs (ordre d'importance)",
        [
            "✅ Acquittement/Relaxe complet",
            "⚖️ Réduction des charges",
            "🤝 Négociation amiable",
            "💰 Minimisation des dommages-intérêts",
            "⏳ Gain de temps procédural",
            "📜 Établir un précédent favorable",
            "🛡️ Protection de la réputation",
            "🔄 Transaction favorable",
            "📊 Éviter le procès"
        ],
        default=["✅ Acquittement/Relaxe complet"],
        help="Sélectionnez jusqu'à 5 objectifs prioritaires"
    )
    
    if len(objectives) > 5:
        st.warning("⚠️ Limitez-vous à 5 objectifs maximum pour une stratégie focalisée")
    
    # Section 5: Configuration avancée avec accordéon
    with st.expander("⚙️ **Configuration avancée de génération**", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### 📚 Recherche & Analyse")
            include_jurisprudence = st.checkbox("🔍 Recherche jurisprudentielle approfondie", value=True)
            include_doctrine = st.checkbox("📖 Analyse doctrinale", value=False)
            include_comparative = st.checkbox("🌍 Droit comparé", value=False)
        
        with col2:
            st.markdown("##### 📊 Éléments stratégiques")
            include_scenarios = st.checkbox("🔄 Scénarios alternatifs", value=True)
            include_timeline = st.checkbox("📅 Planning détaillé", value=True)
            include_negotiation = st.checkbox("🤝 Stratégie de négociation", value=True)
        
        with col3:
            st.markdown("##### 🛡️ Gestion des risques")
            risk_assessment = st.checkbox("⚠️ Analyse des risques", value=True)
            contingency_plans = st.checkbox("🔄 Plans de contingence", value=True)
            media_strategy = st.checkbox("📰 Stratégie médiatique", value=False)
    
    # Section 6: Bouton de génération stylé
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Vérification de la validité
        is_valid = bool(context and len(context) > 50)
        
        if not is_valid:
            st.info("💡 Décrivez l'affaire en au moins 50 caractères pour générer une stratégie")
        
        # Bouton animé
        if st.button(
            "🚀 Générer la stratégie avec l'IA",
            type="primary",
            use_container_width=True,
            disabled=not is_valid or st.session_state.strategy_state['generation_in_progress']
        ):
            # Préparer la configuration
            config = {
                'case_type': case_type,
                'urgency': urgency,
                'complexity': complexity,
                'budget': budget,
                'context': context,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'opportunities': opportunities,
                'threats': threats,
                'objectives': objectives,
                'advanced_options': {
                    'include_jurisprudence': include_jurisprudence,
                    'include_doctrine': include_doctrine,
                    'include_comparative': include_comparative,
                    'include_scenarios': include_scenarios,
                    'include_timeline': include_timeline,
                    'include_negotiation': include_negotiation,
                    'risk_assessment': risk_assessment,
                    'contingency_plans': contingency_plans,
                    'media_strategy': media_strategy
                }
            }
            
            # Lancer la génération
            generate_strategy_with_ai(config)

def render_ai_config():
    """Configuration des modèles IA avec interface moderne"""
    
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">🤖 Configuration des Modèles IA</h3>
            <p style="color: #f0f0f0; margin: 5px 0 0 0;">
                Personnalisez l'utilisation des modèles d'intelligence artificielle
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Modèles disponibles avec leurs caractéristiques
    ai_models = {
        'claude-3': {
            'name': 'Claude 3 Opus',
            'provider': 'Anthropic',
            'strengths': ['Raisonnement juridique', 'Analyse contextuelle', 'Éthique'],
            'icon': '🧠',
            'color': '#A23B72'
        },
        'gpt-4': {
            'name': 'GPT-4 Turbo',
            'provider': 'OpenAI',
            'strengths': ['Créativité', 'Argumentation', 'Synthèse'],
            'icon': '🤖',
            'color': '#2E86AB'
        },
        'mistral': {
            'name': 'Mistral Large',
            'provider': 'Mistral AI',
            'strengths': ['Efficacité', 'Multilinguisme', 'Précision'],
            'icon': '⚡',
            'color': '#F18F01'
        },
        'gemini': {
            'name': 'Gemini Pro',
            'provider': 'Google',
            'strengths': ['Recherche', 'Analyse de données', 'Multimodal'],
            'icon': '✨',
            'color': '#4285F4'
        }
    }
    
    # Section 1: Sélection des modèles
    st.markdown("### 🎯 Sélection des modèles")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_models = st.multiselect(
            "Modèles actifs",
            options=list(ai_models.keys()),
            default=st.session_state.strategy_state['ai_models_config']['selected_models'],
            format_func=lambda x: f"{ai_models[x]['icon']} {ai_models[x]['name']}",
            help="Sélectionnez un ou plusieurs modèles à utiliser"
        )
        
        # Mise à jour de l'état
        st.session_state.strategy_state['ai_models_config']['selected_models'] = selected_models
    
    with col2:
        fusion_mode = st.toggle(
            "🔄 Mode Fusion",
            value=st.session_state.strategy_state['ai_models_config']['fusion_mode'],
            help="Combine les réponses de plusieurs modèles pour une stratégie optimale"
        )
        st.session_state.strategy_state['ai_models_config']['fusion_mode'] = fusion_mode
    
    # Affichage des modèles sélectionnés
    if selected_models:
        st.markdown("### 📊 Modèles sélectionnés")
        
        cols = st.columns(len(selected_models))
        
        for idx, (col, model_key) in enumerate(zip(cols, selected_models)):
            model = ai_models[model_key]
            
            with col:
                # Card du modèle
                st.markdown(
                    f"""
                    <div style="background: {model['color']}20; border: 2px solid {model['color']}; 
                                border-radius: 10px; padding: 15px; text-align: center;">
                        <h4 style="color: {model['color']}; margin: 0;">
                            {model['icon']} {model['name']}
                        </h4>
                        <p style="color: #666; font-size: 0.9em; margin: 5px 0;">
                            {model['provider']}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Points forts
                with st.expander("Points forts", expanded=False):
                    for strength in model['strengths']:
                        st.write(f"• {strength}")
    
    # Section 2: Configuration du mode fusion
    if fusion_mode and len(selected_models) > 1:
        st.markdown("### ⚖️ Configuration de la fusion")
        
        st.info("🔄 En mode fusion, les réponses de chaque modèle sont pondérées et combinées pour obtenir la meilleure stratégie possible.")
        
        # Répartition des poids
        st.markdown("#### 📊 Répartition des poids")
        
        weights = {}
        remaining = 100
        
        for i, model_key in enumerate(selected_models[:-1]):
            model = ai_models[model_key]
            
            weight = st.slider(
                f"{model['icon']} {model['name']}",
                min_value=0,
                max_value=remaining,
                value=min(
                    int(100 / len(selected_models)),
                    remaining
                ),
                step=5,
                help=f"Poids accordé à {model['name']} dans la fusion"
            )
            
            weights[model_key] = weight / 100
            remaining -= weight
        
        # Dernier modèle prend le reste
        if selected_models:
            last_model = selected_models[-1]
            weights[last_model] = remaining / 100
            st.metric(
                f"{ai_models[last_model]['icon']} {ai_models[last_model]['name']}",
                f"{remaining}%"
            )
        
        st.session_state.strategy_state['ai_models_config']['weights'] = weights
        
        # Visualisation de la répartition
        if weights:
            st.markdown("#### 📈 Visualisation de la répartition")
            
            # Créer un graphique en barres horizontales simple
            data = []
            for model_key, weight in weights.items():
                data.append({
                    'Modèle': f"{ai_models[model_key]['icon']} {ai_models[model_key]['name']}",
                    'Poids': weight * 100
                })
            
            df = pd.DataFrame(data)
            st.bar_chart(df.set_index('Modèle'))
    
    # Section 3: Stratégies prédéfinies
    st.markdown("### 🎮 Stratégies prédéfinies")
    
    preset_strategies = {
        'balanced': {
            'name': '⚖️ Équilibrée',
            'description': 'Répartition égale entre tous les modèles',
            'config': lambda models: {m: 1/len(models) for m in models}
        },
        'creative': {
            'name': '🎨 Créative',
            'description': 'Favorise GPT-4 pour plus de créativité',
            'config': lambda models: {'gpt-4': 0.5, **{m: 0.5/(len(models)-1) for m in models if m != 'gpt-4'}}
        },
        'analytical': {
            'name': '🔬 Analytique',
            'description': 'Favorise Claude 3 pour l\'analyse approfondie',
            'config': lambda models: {'claude-3': 0.5, **{m: 0.5/(len(models)-1) for m in models if m != 'claude-3'}}
        },
        'fast': {
            'name': '⚡ Rapide',
            'description': 'Favorise Mistral pour la rapidité',
            'config': lambda models: {'mistral': 0.5, **{m: 0.5/(len(models)-1) for m in models if m != 'mistral'}}
        }
    }
    
    cols = st.columns(len(preset_strategies))
    
    for col, (key, preset) in zip(cols, preset_strategies.items()):
        with col:
            if st.button(
                preset['name'],
                use_container_width=True,
                help=preset['description']
            ):
                if fusion_mode and len(selected_models) > 1:
                    # Appliquer la stratégie prédéfinie
                    new_weights = preset['config'](selected_models)
                    
                    # Ajuster pour n'inclure que les modèles sélectionnés
                    adjusted_weights = {}
                    total = 0
                    
                    for model in selected_models:
                        if model in new_weights:
                            adjusted_weights[model] = new_weights[model]
                            total += new_weights[model]
                    
                    # Normaliser si nécessaire
                    if total > 0:
                        for model in adjusted_weights:
                            adjusted_weights[model] /= total
                    
                    st.session_state.strategy_state['ai_models_config']['weights'] = adjusted_weights
                    st.success(f"✅ Stratégie '{preset['name']}' appliquée")
                    st.rerun()
    
    # Section 4: Test des modèles
    st.markdown("### 🧪 Test des modèles")
    
    test_prompt = st.text_area(
        "Prompt de test",
        placeholder="Entrez un prompt juridique pour tester les modèles...",
        height=100
    )
    
    if st.button("🚀 Tester les modèles", disabled=not test_prompt):
        test_ai_models(test_prompt, selected_models, fusion_mode, weights if fusion_mode else None)

def generate_strategy_with_ai(config: Dict[str, Any]):
    """Génère une stratégie en utilisant les modèles IA configurés"""
    
    st.session_state.strategy_state['generation_in_progress'] = True
    
    # Container pour l'affichage de la progression
    progress_container = st.container()
    
    with progress_container:
        # Header de génération
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: white; margin: 0;">🚀 Génération en cours...</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Barre de progression principale
        main_progress = st.progress(0)
        status_text = st.empty()
        
        # Container pour les détails
        details_container = st.container()
        
        # Récupérer la configuration IA
        ai_config = st.session_state.strategy_state['ai_models_config']
        selected_models = ai_config['selected_models']
        fusion_mode = ai_config['fusion_mode']
        weights = ai_config.get('weights', {})
        
        # Phases de génération
        phases = []
        
        # Phase 1: Analyse initiale
        phases.append({
            'name': '📊 Analyse du contexte',
            'duration': 2,
            'substeps': [
                'Extraction des éléments clés',
                'Identification des enjeux juridiques',
                'Analyse SWOT approfondie'
            ]
        })
        
        # Phase 2: Génération par modèle
        if fusion_mode and len(selected_models) > 1:
            for model in selected_models:
                phases.append({
                    'name': f'🤖 Génération {model.upper()}',
                    'duration': 3,
                    'substeps': [
                        'Formulation de la stratégie',
                        'Arguments juridiques',
                        'Plan d\'action'
                    ]
                })
            
            phases.append({
                'name': '🔄 Fusion des stratégies',
                'duration': 2,
                'substeps': [
                    'Analyse comparative',
                    'Synthèse optimale',
                    'Harmonisation'
                ]
            })
        else:
            phases.append({
                'name': f'🤖 Génération IA',
                'duration': 4,
                'substeps': [
                    'Stratégie principale',
                    'Arguments et défense',
                    'Plan d\'action détaillé'
                ]
            })
        
        # Phases optionnelles
        if config['advanced_options']['include_jurisprudence']:
            phases.append({
                'name': '📚 Recherche jurisprudentielle',
                'duration': 2,
                'substeps': [
                    'Analyse des précédents',
                    'Jurisprudence favorable',
                    'Contre-arguments'
                ]
            })
        
        if config['advanced_options']['risk_assessment']:
            phases.append({
                'name': '⚠️ Analyse des risques',
                'duration': 1.5,
                'substeps': [
                    'Identification des risques',
                    'Évaluation impact/probabilité',
                    'Stratégies de mitigation'
                ]
            })
        
        if config['advanced_options']['include_timeline']:
            phases.append({
                'name': '📅 Planning stratégique',
                'duration': 1,
                'substeps': [
                    'Jalons clés',
                    'Allocation ressources',
                    'Calendrier détaillé'
                ]
            })
        
        # Phase finale
        phases.append({
            'name': '✨ Finalisation',
            'duration': 1,
            'substeps': [
                'Synthèse globale',
                'Vérification cohérence',
                'Optimisation finale'
            ]
        })
        
        # Calcul du temps total
        total_duration = sum(phase['duration'] for phase in phases)
        current_progress = 0
        
        # Exécution des phases
        for i, phase in enumerate(phases):
            status_text.markdown(f"**{phase['name']}**")
            
            # Container pour les sous-étapes
            with details_container:
                phase_expander = st.expander(phase['name'], expanded=True)
                
                with phase_expander:
                    # Afficher les sous-étapes
                    substep_containers = []
                    for substep in phase['substeps']:
                        substep_col1, substep_col2 = st.columns([10, 1])
                        with substep_col1:
                            substep_text = st.empty()
                            substep_text.markdown(f"⏳ {substep}")
                        with substep_col2:
                            substep_status = st.empty()
                        
                        substep_containers.append((substep_text, substep_status, substep))
                    
                    # Animation des sous-étapes
                    for j, (text_widget, status_widget, substep_name) in enumerate(substep_containers):
                        # Mise à jour progressive
                        time.sleep(phase['duration'] / len(phase['substeps']) * 0.3)
                        text_widget.markdown(f"🔄 {substep_name}")
                        
                        time.sleep(phase['duration'] / len(phase['substeps']) * 0.7)
                        text_widget.markdown(f"✅ {substep_name}")
                        status_widget.markdown("✓")
                        
                        # Mise à jour de la progression
                        substep_progress = (phase['duration'] / len(phase['substeps'])) / total_duration
                        current_progress += substep_progress
                        main_progress.progress(min(current_progress, 0.99))
        
        # Finalisation
        main_progress.progress(1.0)
        status_text.markdown("**✅ Stratégie générée avec succès !**")
        time.sleep(0.5)
        
        # Nettoyer l'affichage de progression
        progress_container.empty()
    
    # Générer la stratégie
    strategy = create_strategy_from_config(config, selected_models, fusion_mode, weights)
    
    # Sauvegarder la stratégie
    st.session_state.strategy_state['current_strategy'] = strategy
    st.session_state.strategy_state['strategy_history'].append(strategy)
    st.session_state.strategy_state['generation_in_progress'] = False
    
    # Afficher la stratégie
    display_strategy(strategy)

def create_strategy_from_config(config: Dict[str, Any], models: List[str], fusion_mode: bool, weights: Dict[str, float]) -> Dict[str, Any]:
    """Crée une stratégie complète basée sur la configuration"""
    
    templates = get_strategy_templates()
    template = templates[config['case_type']]
    
    # Structure de base de la stratégie
    strategy = {
        'id': f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
        'created_at': datetime.now(),
        'config': config,
        'ai_models_used': models,
        'fusion_mode': fusion_mode,
        'weights': weights if fusion_mode else None,
        'metadata': {
            'version': '2.0',
            'template': template['name'],
            'urgency_level': config['urgency'],
            'complexity_level': config['complexity'],
            'budget_level': config['budget']
        }
    }
    
    # Générer les composants de la stratégie
    strategy['main_approach'] = generate_main_approach(config, template)
    strategy['action_plan'] = generate_action_plan(config)
    strategy['arguments'] = generate_legal_arguments(config)
    
    # Composants optionnels
    if config['advanced_options']['risk_assessment']:
        strategy['risks'] = assess_risks(config)
    
    if config['advanced_options']['include_scenarios']:
        strategy['scenarios'] = generate_scenarios(config)
    
    if config['advanced_options']['include_timeline']:
        strategy['timeline'] = generate_timeline(config)
    
    if config['advanced_options']['include_negotiation']:
        strategy['negotiation'] = generate_negotiation_strategy(config)
    
    if config['advanced_options']['include_jurisprudence']:
        strategy['jurisprudence'] = search_jurisprudence(config)
    
    strategy['resources'] = estimate_resources(config)
    strategy['success_metrics'] = define_success_metrics(config)
    
    return strategy

def display_strategy(strategy: Dict[str, Any]):
    """Affiche la stratégie générée avec un design moderne"""
    
    # Header avec informations clés
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); 
                    padding: 25px; border-radius: 15px; margin-bottom: 25px;">
            <h2 style="color: white; margin: 0;">📋 {strategy['main_approach']['title']}</h2>
            <p style="color: #f0f0f0; margin: 10px 0 0 0;">
                Générée le {strategy['created_at'].strftime('%d/%m/%Y à %H:%M')} | 
                ID: {strategy['id'][-8:]}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Métriques principales avec design cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        urgency_colors = {
            '🟢 Faible': ('green', '🟢'),
            '🟡 Modérée': ('orange', '🟡'),
            '🟠 Élevée': ('darkorange', '🟠'),
            '🔴 Critique': ('red', '🔴')
        }
        color, icon = urgency_colors.get(strategy['config']['urgency'], ('gray', '⚪'))
        
        st.markdown(
            f"""
            <div style="background: {color}20; border: 2px solid {color}; 
                        border-radius: 10px; padding: 15px; text-align: center;">
                <h4 style="color: {color}; margin: 0;">{icon} Urgence</h4>
                <p style="margin: 5px 0 0 0;">{strategy['config']['urgency'].split()[1]}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        if strategy.get('risks'):
            risk_colors = {
                'Faible': ('green', '🟢'),
                'Modéré': ('orange', '🟡'),
                'Élevé': ('red', '🔴')
            }
            color, icon = risk_colors.get(strategy['risks']['level'], ('gray', '⚪'))
            
            st.markdown(
                f"""
                <div style="background: {color}20; border: 2px solid {color}; 
                            border-radius: 10px; padding: 15px; text-align: center;">
                    <h4 style="color: {color}; margin: 0;">{icon} Risque</h4>
                    <p style="margin: 5px 0 0 0;">{strategy['risks']['level']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with col3:
        st.markdown(
            f"""
            <div style="background: #667eea20; border: 2px solid #667eea; 
                        border-radius: 10px; padding: 15px; text-align: center;">
                <h4 style="color: #667eea; margin: 0;">📋 Actions</h4>
                <p style="margin: 5px 0 0 0;">{len(strategy['action_plan'])} phases</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"""
            <div style="background: #4CAF5020; border: 2px solid #4CAF50; 
                        border-radius: 10px; padding: 15px; text-align: center;">
                <h4 style="color: #4CAF50; margin: 0;">💰 Budget</h4>
                <p style="margin: 5px 0 0 0;">{strategy['resources']['budget_estimate'].split('-')[0].strip()}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col5:
        models_text = ", ".join(strategy['ai_models_used'])
        st.markdown(
            f"""
            <div style="background: #FF6B6B20; border: 2px solid #FF6B6B; 
                        border-radius: 10px; padding: 15px; text-align: center;">
                <h4 style="color: #FF6B6B; margin: 0;">🤖 IA</h4>
                <p style="margin: 5px 0 0 0; font-size: 0.8em;">{models_text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Tabs élégants pour le contenu
    tab_list = [
        "🎯 Vue d'ensemble",
        "📋 Plan d'action",
        "💭 Arguments",
        "⚠️ Risques",
        "🔄 Scénarios",
        "📅 Planning",
        "🤝 Négociation",
        "👥 Ressources",
        "📊 Métriques",
        "💾 Export"
    ]
    
    # Filtrer les tabs selon les options activées
    active_tabs = ["🎯 Vue d'ensemble", "📋 Plan d'action", "💭 Arguments"]
    
    if strategy.get('risks'):
        active_tabs.append("⚠️ Risques")
    if strategy.get('scenarios'):
        active_tabs.append("🔄 Scénarios")
    if strategy.get('timeline'):
        active_tabs.append("📅 Planning")
    if strategy.get('negotiation'):
        active_tabs.append("🤝 Négociation")
    
    active_tabs.extend(["👥 Ressources", "📊 Métriques", "💾 Export"])
    
    tabs = st.tabs(active_tabs)
    
    # Contenu des tabs
    tab_index = 0
    
    # Vue d'ensemble
    with tabs[tab_index]:
        display_overview_tab(strategy)
    tab_index += 1
    
    # Plan d'action
    with tabs[tab_index]:
        display_action_plan_tab(strategy)
    tab_index += 1
    
    # Arguments
    with tabs[tab_index]:
        display_arguments_tab(strategy)
    tab_index += 1
    
    # Tabs conditionnels
    if strategy.get('risks'):
        with tabs[tab_index]:
            display_risks_tab(strategy)
        tab_index += 1
    
    if strategy.get('scenarios'):
        with tabs[tab_index]:
            display_scenarios_tab(strategy)
        tab_index += 1
    
    if strategy.get('timeline'):
        with tabs[tab_index]:
            display_timeline_tab(strategy)
        tab_index += 1
    
    if strategy.get('negotiation'):
        with tabs[tab_index]:
            display_negotiation_tab(strategy)
        tab_index += 1
    
    # Tabs finaux
    with tabs[tab_index]:
        display_resources_tab(strategy)
    tab_index += 1
    
    with tabs[tab_index]:
        display_metrics_tab(strategy)
    tab_index += 1
    
    with tabs[tab_index]:
        display_export_tab(strategy)

def display_overview_tab(strategy: Dict[str, Any]):
    """Affiche la vue d'ensemble de la stratégie"""
    
    # Message clé
    st.markdown(
        f"""
        <div style="background: #E8F4F8; border-left: 4px solid #2E86AB; 
                    padding: 20px; border-radius: 5px; margin-bottom: 20px;">
            <h4 style="color: #2E86AB; margin: 0;">💬 Message clé</h4>
            <p style="font-size: 1.1em; margin: 10px 0 0 0; font-style: italic;">
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
        st.write(strategy['main_approach']['narrative'])
        
        st.markdown("#### 📍 Axes prioritaires")
        for i, axis in enumerate(strategy['main_approach']['primary_axes'], 1):
            st.markdown(
                f"""
                <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>{i}.</strong> {axis}
                </div>
                """,
                unsafe_allow_html=True
            )
    
    with col2:
        # Objectifs
        st.markdown("### 🎯 Objectifs visés")
        for obj in strategy['config']['objectives'][:5]:
            st.markdown(f"• {obj}")
        
        # Modèles IA utilisés
        if strategy['fusion_mode'] and strategy['weights']:
            st.markdown("### 🤖 Contribution IA")
            for model, weight in strategy['weights'].items():
                st.progress(weight, text=f"{model}: {int(weight*100)}%")

def display_action_plan_tab(strategy: Dict[str, Any]):
    """Affiche le plan d'action détaillé"""
    
    st.markdown("### 📋 Plan d'action stratégique")
    
    # Timeline visuelle
    for i, phase in enumerate(strategy['action_plan']):
        # Couleur selon la priorité
        priority_colors = {
            'Critique': '#FF4B4B',
            'Élevée': '#FFA500',
            'Normale': '#4B8BFF',
            'Stratégique': '#4CAF50'
        }
        color = priority_colors.get(phase['priority'], '#666')
        
        # Card de phase
        with st.expander(f"**Phase {i+1}: {phase['phase']}**", expanded=(i == 0)):
            # Header de phase
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(
                    f"""
                    <span style="background: {color}; color: white; 
                                padding: 5px 10px; border-radius: 20px; font-size: 0.9em;">
                        Priorité {phase['priority']}
                    </span>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(f"**Durée estimée:** {phase.get('duration', 'À définir')}")
            
            # Tâches avec checkboxes
            st.markdown("#### 📌 Tâches à accomplir")
            
            for j, task in enumerate(phase['tasks']):
                task_id = f"task_{strategy['id']}_{i}_{j}"
                completed = st.checkbox(task, key=task_id)
                
                if completed:
                    st.markdown(
                        f'<span style="text-decoration: line-through; color: #888;">{task}</span>',
                        unsafe_allow_html=True
                    )
            
            # Ressources nécessaires
            if phase.get('resources'):
                st.markdown("#### 👥 Ressources nécessaires")
                for resource in phase['resources']:
                    st.write(f"• {resource}")
            
            # Livrables attendus
            if phase.get('deliverables'):
                st.markdown("#### 📄 Livrables")
                for deliverable in phase['deliverables']:
                    st.write(f"• {deliverable}")

def display_arguments_tab(strategy: Dict[str, Any]):
    """Affiche les arguments juridiques avec style"""
    
    st.markdown("### 💭 Arsenal argumentaire")
    
    arguments = strategy['arguments']
    
    # Arguments principaux avec cards
    st.markdown("#### ⚖️ Arguments principaux")
    
    for i, arg in enumerate(arguments['principaux'], 1):
        st.markdown(
            f"""
            <div style="background: #E8F4F8; border-left: 4px solid #2E86AB; 
                        padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h5 style="color: #2E86AB; margin: 0;">Argument #{i}</h5>
                <p style="margin: 10px 0 0 0;">{arg['title']}</p>
                <p style="color: #666; font-size: 0.9em; margin: 5px 0 0 0;">
                    {arg['description']}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Preuves à l'appui
        if arg.get('supporting_evidence'):
            with st.expander("📁 Preuves à l'appui"):
                for evidence in arg['supporting_evidence']:
                    st.write(f"• {evidence}")
    
    # Arguments subsidiaires
    if arguments.get('subsidiaires'):
        st.markdown("#### 🔄 Arguments subsidiaires")
        
        cols = st.columns(2)
        for i, arg in enumerate(arguments['subsidiaires']):
            with cols[i % 2]:
                st.info(f"**{i+1}.** {arg}")
    
    # Anticipation des contre-arguments
    if arguments.get('contra'):
        st.markdown("#### 🛡️ Réfutation anticipée")
        
        for counter in arguments['contra']:
            with st.expander(f"⚠️ {counter['opposing_argument']}"):
                st.write(f"**Notre réponse:** {counter['rebuttal']}")
                
                if counter.get('legal_basis'):
                    st.write(f"**Base juridique:** {counter['legal_basis']}")

def display_risks_tab(strategy: Dict[str, Any]):
    """Affiche l'analyse des risques avec visualisations"""
    
    if not strategy.get('risks'):
        st.info("Analyse des risques non demandée")
        return
    
    risks = strategy['risks']
    
    # Niveau de risque global avec gauge visuel
    st.markdown("### ⚠️ Analyse des risques")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Indicateur visuel du niveau de risque
        risk_levels = {
            'Faible': {'color': '#4CAF50', 'value': 25, 'icon': '🟢'},
            'Modéré': {'color': '#FFA500', 'value': 50, 'icon': '🟡'},
            'Élevé': {'color': '#FF4B4B', 'value': 75, 'icon': '🔴'},
            'Critique': {'color': '#8B0000', 'value': 100, 'icon': '⚫'}
        }
        
        level_info = risk_levels.get(risks['level'], risk_levels['Modéré'])
        
        st.markdown(
            f"""
            <div style="text-align: center; padding: 20px;">
                <h2 style="color: {level_info['color']};">
                    {level_info['icon']} Niveau de risque : {risks['level']}
                </h2>
                <div style="background: #e0e0e0; border-radius: 10px; height: 20px; margin: 20px 0;">
                    <div style="background: {level_info['color']}; width: {level_info['value']}%; 
                                height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Matrice des risques
    st.markdown("#### 📊 Matrice des risques")
    
    # Créer une grille de risques
    risk_matrix_data = []
    for factor in risks['factors']:
        risk_matrix_data.append({
            'Risque': factor['type'],
            'Probabilité': factor.get('probability', 50),
            'Impact': factor.get('impact', 50),
            'Score': factor.get('probability', 50) * factor.get('impact', 50) / 100
        })
    
    df_risks = pd.DataFrame(risk_matrix_data)
    
    # Afficher sous forme de tableau coloré
    st.dataframe(
        df_risks.style.background_gradient(subset=['Score'], cmap='RdYlGn_r'),
        use_container_width=True,
        hide_index=True
    )
    
    # Détail des risques
    st.markdown("#### 📋 Analyse détaillée")
    
    for i, factor in enumerate(risks['factors']):
        severity_colors = {
            'Faible': 'green',
            'Modérée': 'orange',
            'Élevée': 'red',
            'Critique': 'darkred'
        }
        color = severity_colors.get(factor['severity'], 'gray')
        
        with st.expander(
            f"{factor['severity_icon']} **{factor['type']}** - Sévérité: {factor['severity']}",
            expanded=(factor['severity'] in ['Élevée', 'Critique'])
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Description:** {factor['description']}")
                
                if factor.get('consequences'):
                    st.write("**Conséquences potentielles:**")
                    for consequence in factor['consequences']:
                        st.write(f"• {consequence}")
            
            with col2:
                # Indicateurs visuels
                st.metric("Probabilité", f"{factor.get('probability', 50)}%")
                st.metric("Impact", f"{factor.get('impact', 50)}%")
    
    # Stratégies de mitigation
    st.markdown("#### 🛡️ Plan de mitigation")
    
    for i, mitigation in enumerate(risks['mitigation'], 1):
        with st.container():
            st.markdown(
                f"""
                <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; 
                            padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>Mesure {i}:</strong> {mitigation['action']}
                    <br><small style="color: #666;">Efficacité estimée: {mitigation.get('effectiveness', 'Élevée')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

def display_scenarios_tab(strategy: Dict[str, Any]):
    """Affiche les scénarios avec visualisation"""
    
    if not strategy.get('scenarios'):
        st.info("Génération de scénarios non demandée")
        return
    
    st.markdown("### 🔄 Scénarios stratégiques")
    
    # Vue d'ensemble des scénarios
    scenarios_data = []
    for scenario in strategy['scenarios']:
        scenarios_data.append({
            'Scénario': scenario['name'],
            'Probabilité': int(scenario['probability'].rstrip('%')),
            'Impact': scenario.get('impact', 'Moyen')
        })
    
    df_scenarios = pd.DataFrame(scenarios_data)
    
    # Graphique de probabilités
    st.bar_chart(df_scenarios.set_index('Scénario')['Probabilité'])
    
    # Détail de chaque scénario
    for scenario in strategy['scenarios']:
        # Couleur selon la nature du scénario
        if 'favorable' in scenario['name'].lower():
            color = '#4CAF50'
            icon = '✅'
        elif 'défavorable' in scenario['name'].lower() or 'pessimiste' in scenario['name'].lower():
            color = '#FF4B4B'
            icon = '⚠️'
        else:
            color = '#FFA500'
            icon = '📊'
        
        with st.expander(
            f"{icon} **{scenario['name']}** - Probabilité: {scenario['probability']}",
            expanded=(scenario.get('is_most_likely', False))
        ):
            # Description et outcome
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Description:** {scenario['description']}")
                st.write(f"**Résultat attendu:** {scenario['outcome']}")
                
                if scenario.get('duration'):
                    st.write(f"**Durée estimée:** {scenario['duration']}")
            
            with col2:
                # Gauge de probabilité
                prob_value = int(scenario['probability'].rstrip('%'))
                st.metric("Probabilité", scenario['probability'])
                st.progress(prob_value / 100)
            
            # Conditions de réalisation
            st.write("**Conditions de réalisation:**")
            for condition in scenario['conditions']:
                st.write(f"• {condition}")
            
            # Plan d'action spécifique
            if scenario.get('action_plan'):
                st.write("**Actions recommandées:**")
                for action in scenario['action_plan']:
                    st.write(f"📌 {action}")
            
            # Contingence
            if scenario.get('contingency'):
                st.warning(f"**Plan B:** {scenario['contingency']}")

def display_timeline_tab(strategy: Dict[str, Any]):
    """Affiche le planning avec visualisation interactive"""
    
    if not strategy.get('timeline'):
        st.info("Planning non demandé")
        return
    
    st.markdown("### 📅 Planning stratégique")
    
    # Options d'affichage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        view_mode = st.radio(
            "Mode d'affichage",
            ["📊 Chronologique", "📋 Liste", "📈 Gantt"],
            horizontal=True
        )
    
    # Affichage selon le mode choisi
    if view_mode == "📊 Chronologique":
        # Timeline verticale
        for i, milestone in enumerate(strategy['timeline']):
            # Calculer le statut
            days_until = (milestone['target_date'] - datetime.now()).days
            
            if days_until < 0:
                status_color = 'red'
                status_text = 'En retard'
                status_icon = '⚠️'
            elif days_until < 7:
                status_color = 'orange'
                status_text = 'Urgent'
                status_icon = '⏰'
            else:
                status_color = 'green'
                status_text = 'Dans les temps'
                status_icon = '✅'
            
            # Card du milestone
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 10px;">
                            <h2 style="color: {status_color};">{status_icon}</h2>
                            <p style="font-size: 0.8em;">{status_text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col2:
                    st.markdown(f"**{milestone['milestone']}**")
                    st.write(f"📅 {milestone['target_date'].strftime('%d/%m/%Y')}")
                    st.write(f"👤 {milestone['responsible']}")
                    
                    # Progress bar pour ce milestone
                    if milestone.get('completion'):
                        st.progress(milestone['completion'] / 100, 
                                  text=f"Progression: {milestone['completion']}%")
                
                with col3:
                    # Actions
                    if st.button("📝 Détails", key=f"details_{i}"):
                        with st.expander("Livrables", expanded=True):
                            for deliverable in milestone['deliverables']:
                                st.checkbox(deliverable, key=f"del_{i}_{deliverable}")
            
            # Ligne de séparation
            if i < len(strategy['timeline']) - 1:
                st.markdown(
                    """
                    <div style="text-align: center; margin: 20px 0;">
                        <div style="width: 2px; height: 40px; background: #ddd; 
                                    margin: 0 auto;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    elif view_mode == "📋 Liste":
        # Tableau détaillé
        timeline_data = []
        for milestone in strategy['timeline']:
            timeline_data.append({
                'Jalon': milestone['milestone'],
                'Date cible': milestone['target_date'].strftime('%d/%m/%Y'),
                'Responsable': milestone['responsible'],
                'Statut': milestone.get('status', 'À venir'),
                'Progression': f"{milestone.get('completion', 0)}%"
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        st.dataframe(df_timeline, use_container_width=True, hide_index=True)
    
    else:  # Gantt
        st.info("Vue Gantt en développement. Utilisez la vue chronologique ou liste.")

def display_negotiation_tab(strategy: Dict[str, Any]):
    """Affiche la stratégie de négociation"""
    
    if not strategy.get('negotiation'):
        st.info("Stratégie de négociation non demandée")
        return
    
    negotiation = strategy['negotiation']
    
    st.markdown("### 🤝 Stratégie de négociation")
    
    # Position de négociation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            """
            <div style="background: #f0f9ff; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #3b82f6; margin: 0;">🎯 Position idéale</h4>
                <p style="margin: 10px 0 0 0;">{}</p>
            </div>
            """.format(negotiation['ideal_position']),
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div style="background: #fef3c7; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #f59e0b; margin: 0;">🤝 Zone d'accord</h4>
                <p style="margin: 10px 0 0 0;">{}</p>
            </div>
            """.format(negotiation['acceptable_range']),
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            """
            <div style="background: #fee2e2; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #ef4444; margin: 0;">🚫 Ligne rouge</h4>
                <p style="margin: 10px 0 0 0;">{}</p>
            </div>
            """.format(negotiation['red_line']),
            unsafe_allow_html=True
        )
    
    # Tactiques de négociation
    st.markdown("#### 🎭 Tactiques recommandées")
    
    for i, tactic in enumerate(negotiation['tactics'], 1):
        with st.expander(f"Tactique {i}: {tactic['name']}", expanded=(i == 1)):
            st.write(f"**Description:** {tactic['description']}")
            st.write(f"**Quand l'utiliser:** {tactic['when_to_use']}")
            st.write(f"**Avantages:** {tactic['advantages']}")
            st.write(f"**Risques:** {tactic['risks']}")
    
    # Points de négociation
    st.markdown("#### 📋 Points de négociation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### ✅ Négociables")
        for point in negotiation['negotiable_points']:
            st.write(f"• {point}")
    
    with col2:
        st.markdown("##### ❌ Non négociables")
        for point in negotiation['non_negotiable_points']:
            st.write(f"• {point}")
    
    # Calendrier de négociation
    if negotiation.get('negotiation_timeline'):
        st.markdown("#### 📅 Calendrier de négociation")
        
        for phase in negotiation['negotiation_timeline']:
            st.write(f"**{phase['phase']}** - {phase['duration']}")
            st.write(f"Objectifs: {phase['objectives']}")

def display_resources_tab(strategy: Dict[str, Any]):
    """Affiche les ressources nécessaires"""
    
    resources = strategy['resources']
    
    st.markdown("### 👥 Ressources nécessaires")
    
    # Vue d'ensemble avec metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👥 Équipe",
            len(resources['team']),
            f"{resources['team_size_assessment']}"
        )
    
    with col2:
        st.metric(
            "⏱️ Temps estimé",
            resources['time_estimate'],
            "Total cumulé"
        )
    
    with col3:
        st.metric(
            "💰 Budget",
            resources['budget_estimate'].split('-')[0].strip(),
            "Fourchette basse"
        )
    
    with col4:
        st.metric(
            "🔗 Externes",
            len(resources.get('external_needs', [])),
            "Besoins identifiés"
        )
    
    # Détail de l'équipe
    st.markdown("#### 👨‍⚖️ Composition de l'équipe")
    
    team_data = []
    for member in resources['team']:
        team_data.append({
            'Rôle': member['role'],
            'Séniorité': member['seniority'],
            'Temps alloué': member['time_allocation'],
            'Responsabilités': ', '.join(member['responsibilities'][:3])
        })
    
    df_team = pd.DataFrame(team_data)
    st.dataframe(df_team, use_container_width=True, hide_index=True)
    
    # Répartition du budget
    st.markdown("#### 💰 Ventilation budgétaire")
    
    budget_breakdown = resources.get('budget_breakdown', {})
    if budget_breakdown:
        # Créer un graphique en camembert simple
        breakdown_data = []
        for category, amount in budget_breakdown.items():
            breakdown_data.append({
                'Catégorie': category,
                'Montant': amount
            })
        
        df_budget = pd.DataFrame(breakdown_data)
        st.bar_chart(df_budget.set_index('Catégorie'))
    
    # Besoins externes
    if resources.get('external_needs'):
        st.markdown("#### 🔗 Ressources externes")
        
        for need in resources['external_needs']:
            with st.expander(f"📌 {need['type']}"):
                st.write(f"**Description:** {need['description']}")
                st.write(f"**Justification:** {need['justification']}")
                st.write(f"**Coût estimé:** {need['estimated_cost']}")
                st.write(f"**Délai:** {need['timeline']}")

def display_metrics_tab(strategy: Dict[str, Any]):
    """Affiche les métriques de succès"""
    
    metrics = strategy.get('success_metrics', {})
    
    st.markdown("### 📊 Métriques de succès")
    
    # KPIs principaux
    st.markdown("#### 🎯 Indicateurs clés de performance")
    
    kpis = metrics.get('kpis', [])
    
    cols = st.columns(len(kpis[:4]))  # Max 4 KPIs sur une ligne
    
    for col, kpi in zip(cols, kpis[:4]):
        with col:
            # Calculer la couleur selon la cible
            if kpi.get('current_value') and kpi.get('target_value'):
                achievement = (kpi['current_value'] / kpi['target_value']) * 100
                if achievement >= 100:
                    color = 'green'
                elif achievement >= 70:
                    color = 'orange'
                else:
                    color = 'red'
            else:
                color = 'gray'
            
            st.markdown(
                f"""
                <div style="background: {color}20; border: 2px solid {color}; 
                            border-radius: 10px; padding: 15px; text-align: center;">
                    <h5 style="margin: 0;">{kpi['name']}</h5>
                    <h3 style="color: {color}; margin: 10px 0;">
                        {kpi.get('current_value', '-')} / {kpi['target_value']}
                    </h3>
                    <p style="font-size: 0.9em; margin: 0;">{kpi['unit']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Critères de succès
    st.markdown("#### ✅ Critères de succès")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🏆 Succès total")
        for criterion in metrics.get('success_criteria', []):
            st.write(f"✓ {criterion}")
    
    with col2:
        st.markdown("##### 🎯 Succès partiel")
        for criterion in metrics.get('partial_success_criteria', []):
            st.write(f"• {criterion}")
    
    # Tableau de bord de suivi
    st.markdown("#### 📈 Tableau de bord")
    
    # Simuler des données de progression
    progress_data = []
    for phase in strategy['action_plan']:
        progress_data.append({
            'Phase': phase['phase'],
            'Progression': random.randint(0, 100),
            'Statut': random.choice(['En cours', 'Terminé', 'À venir']),
            'Performance': random.choice(['⭐⭐⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐'])
        })
    
    df_progress = pd.DataFrame(progress_data)
    st.dataframe(
        df_progress.style.background_gradient(subset=['Progression'], cmap='Greens'),
        use_container_width=True,
        hide_index=True
    )

def display_export_tab(strategy: Dict[str, Any]):
    """Options d'export avancées"""
    
    st.markdown("### 💾 Export et partage")
    
    # Formats d'export
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 PDF Complet", use_container_width=True):
            pdf_content = generate_pdf_report(strategy)
            st.download_button(
                "⬇️ Télécharger PDF",
                data=pdf_content,
                file_name=f"strategie_{strategy['id'][-8:]}.pdf",
                mime="application/pdf"
            )
    
    with col2:
        if st.button("📝 Word (DOCX)", use_container_width=True):
            docx_content = generate_docx_report(strategy)
            st.download_button(
                "⬇️ Télécharger DOCX",
                data=docx_content,
                file_name=f"strategie_{strategy['id'][-8:]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    
    with col3:
        if st.button("📊 Excel détaillé", use_container_width=True):
            excel_content = generate_excel_report(strategy)
            st.download_button(
                "⬇️ Télécharger Excel",
                data=excel_content,
                file_name=f"strategie_{strategy['id'][-8:]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col4:
        if st.button("💾 JSON brut", use_container_width=True):
            json_str = json.dumps(strategy, default=str, ensure_ascii=False, indent=2)
            st.download_button(
                "⬇️ Télécharger JSON",
                data=json_str,
                file_name=f"strategie_{strategy['id'][-8:]}.json",
                mime="application/json"
            )
    
    # Options de personnalisation
    with st.expander("⚙️ Options d'export", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📄 Sections à inclure")
            include_overview = st.checkbox("Vue d'ensemble", value=True)
            include_arguments = st.checkbox("Arguments détaillés", value=True)
            include_timeline = st.checkbox("Planning", value=True)
            include_risks = st.checkbox("Analyse des risques", value=True)
        
        with col2:
            st.markdown("##### 🎨 Format")
            include_branding = st.checkbox("Inclure logo/en-tête", value=True)
            include_toc = st.checkbox("Table des matières", value=True)
            include_appendix = st.checkbox("Annexes", value=False)
            confidential = st.checkbox("Mention confidentiel", value=True)
    
    # Partage sécurisé
    st.markdown("#### 🔐 Partage sécurisé")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Email
        email_recipients = st.text_input(
            "📧 Destinataires email",
            placeholder="email1@example.com, email2@example.com"
        )
        
        if st.button("📤 Envoyer par email", use_container_width=True):
            if email_recipients:
                st.success("✅ Email envoyé avec succès")
            else:
                st.error("Veuillez entrer au moins une adresse email")
    
    with col2:
        # Lien de partage
        if st.button("🔗 Générer lien sécurisé", use_container_width=True):
            share_link = f"https://nexora-law.ai/share/{strategy['id'][-8:]}"
            st.code(share_link)
            
            # Options du lien
            expiry = st.select_slider(
                "Expiration du lien",
                ["1 jour", "3 jours", "7 jours", "30 jours", "Jamais"]
            )
            password_protect = st.checkbox("Protection par mot de passe")
            
            if password_protect:
                st.text_input("Mot de passe", type="password")

def render_strategy_library():
    """Affiche la bibliothèque de stratégies avec design moderne"""
    
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">📚 Bibliothèque de stratégies</h3>
            <p style="color: #f0f0f0; margin: 5px 0 0 0;">
                Retrouvez et gérez toutes vos stratégies générées
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if not st.session_state.strategy_state.get('strategy_history'):
        st.info("📭 Aucune stratégie sauvegardée. Créez votre première stratégie pour commencer.")
        return
    
    # Barre de recherche et filtres
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        search = st.text_input(
            "🔍 Rechercher",
            placeholder="Mots-clés, ID, type d'affaire...",
            label_visibility="collapsed"
        )
    
    with col2:
        filter_type = st.selectbox(
            "Type",
            ["Tous"] + list(get_strategy_templates().keys()),
            label_visibility="collapsed"
        )
    
    with col3:
        filter_urgency = st.selectbox(
            "Urgence",
            ["Toutes", "🟢 Faible", "🟡 Modérée", "🟠 Élevée", "🔴 Critique"],
            label_visibility="collapsed"
        )
    
    with col4:
        sort_by = st.selectbox(
            "Trier par",
            ["Plus récent", "Plus ancien", "Urgence", "Complexité"],
            label_visibility="collapsed"
        )
    
    # Filtrer les stratégies
    strategies = st.session_state.strategy_state['strategy_history'].copy()
    
    # Appliquer les filtres
    if search:
        strategies = [
            s for s in strategies
            if search.lower() in s['config']['context'].lower() or
               search.lower() in s['id'].lower()
        ]
    
    if filter_type != "Tous":
        strategies = [
            s for s in strategies
            if s['config']['case_type'] == filter_type
        ]
    
    if filter_urgency != "Toutes":
        strategies = [
            s for s in strategies
            if s['config']['urgency'] == filter_urgency
        ]
    
    # Trier
    if sort_by == "Plus récent":
        strategies.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Plus ancien":
        strategies.sort(key=lambda x: x['created_at'])
    elif sort_by == "Urgence":
        urgency_order = ['🔴 Critique', '🟠 Élevée', '🟡 Modérée', '🟢 Faible']
        strategies.sort(key=lambda x: urgency_order.index(x['config']['urgency']))
    
    # Affichage en grille
    st.markdown(f"### 📊 {len(strategies)} stratégie(s) trouvée(s)")
    
    # Vue en cards
    cols = st.columns(2)
    
    for idx, strategy in enumerate(strategies):
        with cols[idx % 2]:
            # Card de stratégie
            template = get_strategy_templates()[strategy['config']['case_type']]
            
            # Couleur selon l'urgence
            urgency_colors = {
                '🟢 Faible': '#4CAF50',
                '🟡 Modérée': '#FFA500',
                '🟠 Élevée': '#FF8C00',
                '🔴 Critique': '#FF4B4B'
            }
            border_color = urgency_colors.get(strategy['config']['urgency'], '#666')
            
            st.markdown(
                f"""
                <div style="border: 2px solid {border_color}; border-radius: 10px; 
                            padding: 15px; margin-bottom: 15px;">
                    <h4 style="margin: 0;">
                        {template['icon']} {template['name']}
                    </h4>
                    <p style="color: #666; font-size: 0.9em; margin: 5px 0;">
                        ID: {strategy['id'][-8:]} | {strategy['created_at'].strftime('%d/%m/%Y %H:%M')}
                    </p>
                    <p style="margin: 10px 0;">
                        {truncate_text(strategy['config']['context'], 150)}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Actions
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("👁️ Voir", key=f"view_{strategy['id']}", use_container_width=True):
                    st.session_state.strategy_state['current_strategy'] = strategy
                    display_strategy(strategy)
            
            with col_b:
                if st.button("📋 Dupliquer", key=f"dup_{strategy['id']}", use_container_width=True):
                    duplicate_strategy(strategy)
            
            with col_c:
                if st.button("🗑️", key=f"del_{strategy['id']}", use_container_width=True):
                    if st.checkbox(f"Confirmer suppression", key=f"conf_del_{strategy['id']}"):
                        st.session_state.strategy_state['strategy_history'].remove(strategy)
                        st.rerun()

def render_strategy_comparison():
    """Interface de comparaison de stratégies"""
    
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">🔄 Comparaison de stratégies</h3>
            <p style="color: #f0f0f0; margin: 5px 0 0 0;">
                Analysez et comparez plusieurs approches stratégiques
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    strategies = st.session_state.strategy_state.get('strategy_history', [])
    
    if len(strategies) < 2:
        st.info("📊 Au moins 2 stratégies sont nécessaires pour effectuer une comparaison.")
        
        if st.button("🎯 Créer une nouvelle stratégie"):
            st.session_state.selected_tab = 0
            st.rerun()
        return
    
    # Sélection des stratégies
    st.markdown("### 🎯 Sélection des stratégies")
    
    # Options de sélection formatées
    options = []
    for s in strategies:
        template = get_strategy_templates()[s['config']['case_type']]
        option = f"{template['icon']} {template['name']} - {s['created_at'].strftime('%d/%m')} - {s['id'][-8:]}"
        options.append(option)
    
    selected_indices = st.multiselect(
        "Choisir 2 à 4 stratégies à comparer",
        range(len(options)),
        format_func=lambda x: options[x],
        max_selections=4,
        help="Sélectionnez les stratégies que vous souhaitez analyser côte à côte"
    )
    
    if len(selected_indices) >= 2:
        selected_strategies = [strategies[i] for i in selected_indices]
        
        # Bouton de comparaison stylé
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(
                "🔍 Lancer la comparaison",
                type="primary",
                use_container_width=True
            ):
                with st.spinner("Analyse comparative en cours..."):
                    time.sleep(1)  # Simulation
                    display_strategy_comparison(selected_strategies)

def display_strategy_comparison(strategies: List[Dict[str, Any]]):
    """Affiche la comparaison détaillée des stratégies"""
    
    st.markdown("### 📊 Analyse comparative")
    
    # Tableau de synthèse
    st.markdown("#### 📋 Vue d'ensemble")
    
    comparison_data = []
    for i, strategy in enumerate(strategies):
        template = get_strategy_templates()[strategy['config']['case_type']]
        
        # Calculer des métriques
        total_actions = sum(len(phase['tasks']) for phase in strategy['action_plan'])
        risk_score = {'Faible': 1, 'Modéré': 2, 'Élevé': 3}.get(
            strategy.get('risks', {}).get('level', 'Modéré'), 2
        )
        
        comparison_data.append({
            'Stratégie': f"S{i+1}: {template['icon']} {template['name'][:15]}...",
            'Urgence': strategy['config']['urgency'].split()[1],
            'Complexité': strategy['config']['complexity'].split()[1],
            'Budget': strategy['config']['budget'].replace('💵', '€'),
            'Actions': total_actions,
            'Risque': strategy.get('risks', {}).get('level', 'N/A'),
            'IA': ', '.join(strategy['ai_models_used'])
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    # Analyse détaillée par aspect
    tabs = st.tabs([
        "🎯 Approches",
        "💭 Arguments",
        "⚠️ Risques",
        "📊 Efficacité",
        "💰 Coûts",
        "🏆 Recommandation"
    ])
    
    with tabs[0]:  # Approches
        st.markdown("#### 🎯 Comparaison des approches")
        
        cols = st.columns(len(strategies))
        
        for col, strategy in zip(cols, strategies):
            with col:
                st.markdown(f"**Stratégie {strategies.index(strategy) + 1}**")
                
                # Axes principaux
                st.write("**Axes prioritaires:**")
                for axis in strategy['main_approach']['primary_axes'][:3]:
                    st.write(f"• {axis}")
                
                # Message clé
                st.info(f'"{strategy["main_approach"]["key_message"][:100]}..."')
    
    with tabs[1]:  # Arguments
        st.markdown("#### 💭 Force argumentaire")
        
        # Matrice des arguments
        arg_comparison = []
        
        for i, strategy in enumerate(strategies):
            args = strategy['arguments']
            arg_comparison.append({
                'Stratégie': f"S{i+1}",
                'Principaux': len(args.get('principaux', [])),
                'Subsidiaires': len(args.get('subsidiaires', [])),
                'Contre-arguments': len(args.get('contra', [])),
                'Score total': len(args.get('principaux', [])) * 3 + 
                             len(args.get('subsidiaires', [])) * 2 + 
                             len(args.get('contra', []))
            })
        
        df_args = pd.DataFrame(arg_comparison)
        st.bar_chart(df_args.set_index('Stratégie')[['Principaux', 'Subsidiaires', 'Contre-arguments']])
        
        # Meilleur score
        best_arg_idx = df_args['Score total'].idxmax()
        st.success(f"💪 La stratégie {best_arg_idx + 1} présente l'arsenal argumentaire le plus complet")
    
    with tabs[2]:  # Risques
        st.markdown("#### ⚠️ Analyse des risques comparée")
        
        risk_data = []
        for i, strategy in enumerate(strategies):
            if strategy.get('risks'):
                risks = strategy['risks']
                risk_data.append({
                    'Stratégie': f"S{i+1}",
                    'Niveau global': risks['level'],
                    'Facteurs identifiés': len(risks['factors']),
                    'Mitigations': len(risks['mitigation'])
                })
        
        if risk_data:
            df_risks = pd.DataFrame(risk_data)
            
            # Graphique des niveaux de risque
            risk_levels = {'Faible': 1, 'Modéré': 2, 'Élevé': 3}
            df_risks['Score'] = df_risks['Niveau global'].map(risk_levels)
            
            st.bar_chart(df_risks.set_index('Stratégie')['Score'])
            
            # Stratégie la moins risquée
            safest = df_risks.loc[df_risks['Score'].idxmin(), 'Stratégie']
            st.success(f"🛡️ La stratégie {safest} présente le profil de risque le plus favorable")
    
    with tabs[3]:  # Efficacité
        st.markdown("#### 📊 Indicateurs d'efficacité")
        
        # Calcul des scores d'efficacité
        efficiency_scores = []
        
        for i, strategy in enumerate(strategies):
            # Calcul basé sur plusieurs critères
            urgency_score = {
                '🟢 Faible': 1, '🟡 Modérée': 2, 
                '🟠 Élevée': 3, '🔴 Critique': 4
            }.get(strategy['config']['urgency'], 2)
            
            complexity_score = {
                '🟢 Simple': 1, '🟡 Modérée': 2,
                '🟠 Complexe': 3, '🔴 Très complexe': 4
            }.get(strategy['config']['complexity'], 2)
            
            # Score d'efficacité (inversé pour urgence et complexité)
            efficiency = (5 - urgency_score) + (5 - complexity_score)
            
            # Bonus pour fusion IA
            if strategy.get('fusion_mode'):
                efficiency += 2
            
            efficiency_scores.append({
                'Stratégie': f"S{i+1}",
                'Score efficacité': efficiency,
                'Temps estimé': strategy['resources']['time_estimate'],
                'Phases': len(strategy['action_plan'])
            })
        
        df_efficiency = pd.DataFrame(efficiency_scores)
        
        # Graphique radar (simulé avec des barres)
        st.bar_chart(df_efficiency.set_index('Stratégie')['Score efficacité'])
    
    with tabs[4]:  # Coûts
        st.markdown("#### 💰 Analyse des coûts")
        
        cost_data = []
        for i, strategy in enumerate(strategies):
            # Extraire le coût minimum de l'estimation
            cost_str = strategy['resources']['budget_estimate']
            min_cost = int(cost_str.split('-')[0].strip().replace(',', '').replace('€', '').strip())
            
            cost_data.append({
                'Stratégie': f"S{i+1}",
                'Coût min': min_cost,
                'Budget': strategy['config']['budget'],
                'Équipe': len(strategy['resources']['team'])
            })
        
        df_costs = pd.DataFrame(cost_data)
        
        # Graphique des coûts
        st.bar_chart(df_costs.set_index('Stratégie')['Coût min'])
        
        # Rapport qualité/prix
        st.markdown("##### 💎 Rapport qualité/prix")
        
        best_value_idx = df_costs['Coût min'].idxmin()
        st.success(f"💰 La stratégie S{best_value_idx + 1} offre le meilleur rapport qualité/prix")
    
    with tabs[5]:  # Recommandation
        st.markdown("#### 🏆 Recommandation finale")
        
        # Analyse multicritères
        scores = {}
        
        for i, strategy in enumerate(strategies):
            score = 0
            
            # Critères d'évaluation
            # Urgence (moins urgent = mieux)
            urgency_score = {
                '🟢 Faible': 3, '🟡 Modérée': 2,
                '🟠 Élevée': 1, '🔴 Critique': 0
            }.get(strategy['config']['urgency'], 1)
            score += urgency_score
            
            # Risque (moins risqué = mieux)
            risk_score = {
                'Faible': 3, 'Modéré': 2, 'Élevé': 1
            }.get(strategy.get('risks', {}).get('level', 'Modéré'), 2)
            score += risk_score
            
            # Nombre d'arguments
            args_count = len(strategy['arguments'].get('principaux', []))
            score += min(args_count, 3)
            
            # Fusion IA
            if strategy.get('fusion_mode'):
                score += 2
            
            scores[f"S{i+1}"] = score
        
        # Stratégie gagnante
        winner = max(scores, key=scores.get)
        winner_idx = int(winner[1]) - 1
        
        # Affichage de la recommandation
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                        padding: 25px; border-radius: 15px; text-align: center;">
                <h2 style="color: white; margin: 0;">
                    🏆 Stratégie recommandée : {winner}
                </h2>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 1.1em;">
                    Score global : {scores[winner]}/12
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Justification
        st.markdown("##### 📝 Justification")
        
        winning_strategy = strategies[winner_idx]
        template = get_strategy_templates()[winning_strategy['config']['case_type']]
        
        justifications = []
        
        if winning_strategy['config']['urgency'] in ['🟢 Faible', '🟡 Modérée']:
            justifications.append("✅ Délais confortables permettant une préparation optimale")
        
        if winning_strategy.get('risks', {}).get('level') == 'Faible':
            justifications.append("✅ Profil de risque maîtrisé")
        
        if winning_strategy.get('fusion_mode'):
            justifications.append("✅ Approche multi-IA pour une stratégie robuste")
        
        if len(winning_strategy['arguments'].get('principaux', [])) >= 3:
            justifications.append("✅ Arsenal argumentaire solide et diversifié")
        
        for justif in justifications:
            st.write(justif)
        
        # Actions recommandées
        st.markdown("##### 🎯 Prochaines étapes recommandées")
        
        st.write("1. **Validation** : Faire valider la stratégie par l'équipe senior")
        st.write("2. **Ressources** : Mobiliser l'équipe selon le plan défini")
        st.write("3. **Lancement** : Démarrer la phase 1 du plan d'action")
        st.write("4. **Suivi** : Mettre en place les KPIs de suivi")

def render_analytics():
    """Dashboard analytique des stratégies"""
    
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">📊 Analytics & Insights</h3>
            <p style="color: #f0f0f0; margin: 5px 0 0 0;">
                Analysez vos performances et tendances stratégiques
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    strategies = st.session_state.strategy_state.get('strategy_history', [])
    
    if not strategies:
        st.info("📊 Aucune donnée disponible. Créez des stratégies pour voir les analytics.")
        return
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📋 Total stratégies",
            len(strategies),
            f"+{len([s for s in strategies if (datetime.now() - s['created_at']).days <= 7])} cette semaine"
        )
    
    with col2:
        # Taux de succès simulé
        success_rate = random.randint(75, 95)
        st.metric(
            "✅ Taux de succès",
            f"{success_rate}%",
            f"+{random.randint(1, 10)}%"
        )
    
    with col3:
        # Temps moyen
        avg_time = sum(int(s['resources']['time_estimate'].split('-')[0]) for s in strategies) / len(strategies)
        st.metric(
            "⏱️ Temps moyen",
            f"{int(avg_time)}h",
            "-15%"
        )
    
    with col4:
        # ROI moyen
        roi = random.randint(250, 450)
        st.metric(
            "💰 ROI moyen",
            f"{roi}%",
            f"+{random.randint(10, 50)}%"
        )
    
    # Graphiques
    tabs = st.tabs([
        "📈 Tendances",
        "🎯 Performance",
        "🤖 Utilisation IA",
        "💼 Types d'affaires",
        "📊 Benchmarks"
    ])
    
    with tabs[0]:  # Tendances
        st.markdown("#### 📈 Évolution temporelle")
        
        # Créer des données de tendance
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            freq='D'
        )
        
        trend_data = pd.DataFrame({
            'Date': dates,
            'Stratégies créées': [random.randint(0, 5) for _ in dates],
            'Taux de succès': [random.randint(70, 95) for _ in dates]
        })
        
        st.line_chart(trend_data.set_index('Date'))
    
    with tabs[1]:  # Performance
        st.markdown("#### 🎯 Indicateurs de performance")
        
        # KPIs par type d'affaire
        perf_by_type = {}
        templates = get_strategy_templates()
        
        for case_type in templates.keys():
            type_strategies = [s for s in strategies if s['config']['case_type'] == case_type]
            if type_strategies:
                perf_by_type[templates[case_type]['name']] = {
                    'Nombre': len(type_strategies),
                    'Succès': random.randint(70, 95)
                }
        
        if perf_by_type:
            df_perf = pd.DataFrame(perf_by_type).T
            st.bar_chart(df_perf)
    
    with tabs[2]:  # Utilisation IA
        st.markdown("#### 🤖 Statistiques d'utilisation des modèles IA")
        
        # Compter l'utilisation des modèles
        model_usage = {}
        fusion_count = 0
        
        for strategy in strategies:
            for model in strategy.get('ai_models_used', []):
                model_usage[model] = model_usage.get(model, 0) + 1
            
            if strategy.get('fusion_mode'):
                fusion_count += 1
        
        if model_usage:
            # Graphique d'utilisation
            df_models = pd.DataFrame(
                list(model_usage.items()),
                columns=['Modèle', 'Utilisations']
            )
            st.bar_chart(df_models.set_index('Modèle'))
            
            # Taux de fusion
            fusion_rate = (fusion_count / len(strategies)) * 100
            st.info(f"🔄 Mode fusion utilisé dans {fusion_rate:.1f}% des stratégies")
    
    with tabs[3]:  # Types d'affaires
        st.markdown("#### 💼 Répartition par type d'affaire")
        
        # Compter par type
        type_counts = {}
        for strategy in strategies:
            case_type = strategy['config']['case_type']
            template = get_strategy_templates()[case_type]
            type_counts[template['name']] = type_counts.get(template['name'], 0) + 1
        
        if type_counts:
            # Créer un graphique en secteurs simulé avec des barres
            df_types = pd.DataFrame(
                list(type_counts.items()),
                columns=['Type', 'Nombre']
            )
            st.bar_chart(df_types.set_index('Type'))
    
    with tabs[4]:  # Benchmarks
        st.markdown("#### 📊 Benchmarks sectoriels")
        
        # Données de benchmark simulées
        benchmark_data = {
            'Votre cabinet': {
                'Taux de succès': success_rate,
                'Temps moyen': int(avg_time),
                'ROI': roi
            },
            'Moyenne sectorielle': {
                'Taux de succès': 82,
                'Temps moyen': 120,
                'ROI': 320
            },
            'Top 10%': {
                'Taux de succès': 94,
                'Temps moyen': 80,
                'ROI': 480
            }
        }
        
        df_benchmark = pd.DataFrame(benchmark_data).T
        st.dataframe(
            df_benchmark.style.background_gradient(cmap='Greens'),
            use_container_width=True
        )
        
        # Recommandations
        st.markdown("##### 💡 Recommandations d'amélioration")
        
        if success_rate < 90:
            st.write("• 📈 Augmenter l'utilisation du mode fusion IA pour améliorer le taux de succès")
        
        if avg_time > 100:
            st.write("• ⏱️ Optimiser les processus pour réduire le temps de traitement")
        
        st.write("• 🎯 Continuer à diversifier les types d'affaires traités")
        st.write("• 🤖 Explorer les nouveaux modèles IA disponibles")

def render_help():
    """Affiche l'aide détaillée du module"""
    
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #9333ea 0%, #c026d3 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">❓ Guide d'utilisation</h3>
            <p style="color: #f0f0f0; margin: 5px 0 0 0;">
                Tout ce que vous devez savoir sur le module Stratégie Juridique IA
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # FAQ avec accordéons
    faqs = [
        {
            'question': "🚀 Comment commencer ?",
            'answer': """
            1. **Nouvelle stratégie** : Cliquez sur l'onglet "Nouvelle stratégie"
            2. **Configuration** : Remplissez les informations de base (type, urgence, complexité)
            3. **Contexte** : Décrivez l'affaire en détail (min. 50 caractères)
            4. **Analyse SWOT** : Identifiez forces, faiblesses, opportunités et menaces
            5. **Génération** : Cliquez sur "Générer la stratégie avec l'IA"
            """
        },
        {
            'question': "🤖 Comment fonctionne le mode fusion IA ?",
            'answer': """
            Le mode fusion combine les réponses de plusieurs modèles d'IA :
            
            • **Activation** : Dans l'onglet "Modèles IA", activez le toggle "Mode Fusion"
            • **Sélection** : Choisissez 2 à 4 modèles différents
            • **Pondération** : Ajustez les poids de chaque modèle (total = 100%)
            • **Résultat** : La stratégie finale intègre le meilleur de chaque modèle
            
            **Avantages** :
            - Plus grande robustesse
            - Perspectives multiples
            - Réduction des biais
            - Créativité accrue
            """
        },
        {
            'question': "📊 Comment interpréter les indicateurs ?",
            'answer': """
            **Urgence** :
            - 🟢 Faible : Plus de 3 mois
            - 🟡 Modérée : 1-3 mois
            - 🟠 Élevée : 2-4 semaines
            - 🔴 Critique : Moins de 2 semaines
            
            **Niveau de risque** :
            - 🟢 Faible : Stratégie sûre, peu d'incertitudes
            - 🟡 Modéré : Quelques défis identifiés
            - 🔴 Élevé : Risques importants nécessitant vigilance
            
            **Complexité** :
            - Impact sur les ressources nécessaires
            - Détermine la profondeur d'analyse
            - Influence le budget estimé
            """
        },
        {
            'question': "💾 Comment exporter une stratégie ?",
            'answer': """
            Dans l'onglet "Export" de chaque stratégie :
            
            **Formats disponibles** :
            - 📄 **PDF** : Document complet avec mise en forme
            - 📝 **Word** : Éditable pour personnalisation
            - 📊 **Excel** : Données structurées pour analyse
            - 💾 **JSON** : Format brut pour intégrations
            
            **Options** :
            - Sélectionner les sections à inclure
            - Ajouter branding personnalisé
            - Protection par mot de passe
            - Envoi direct par email
            """
        },
        {
            'question': "🔄 Comment comparer des stratégies ?",
            'answer': """
            1. Accédez à l'onglet "Comparaison"
            2. Sélectionnez 2 à 4 stratégies
            3. Cliquez sur "Lancer la comparaison"
            
            **Critères analysés** :
            - Approches stratégiques
            - Force argumentaire
            - Profils de risque
            - Efficacité estimée
            - Rapport qualité/prix
            
            Une recommandation finale est fournie basée sur l'analyse multicritères.
            """
        },
        {
            'question': "⚙️ Configuration avancée",
            'answer': """
            **Options disponibles** :
            
            📚 **Recherche jurisprudentielle** :
            - Analyse des précédents pertinents
            - Jurisprudence favorable/défavorable
            
            🔄 **Scénarios alternatifs** :
            - Optimiste (30%)
            - Probable (50%)
            - Pessimiste (20%)
            
            📅 **Planning détaillé** :
            - Jalons avec dates cibles
            - Allocation des ressources
            - Livrables par phase
            
            🤝 **Stratégie de négociation** :
            - Position idéale et limites
            - Tactiques recommandées
            - Points négociables/non négociables
            """
        },
        {
            'question': "🏆 Meilleures pratiques",
            'answer': """
            **Pour des résultats optimaux** :
            
            1. **Contexte détaillé** : Plus c'est précis, meilleure est la stratégie
            2. **Honnêteté SWOT** : N'omettez pas les faiblesses
            3. **Multi-modèles** : Utilisez le mode fusion pour les cas complexes
            4. **Itération** : Affinez la stratégie au fil du temps
            5. **Documentation** : Exportez et archivez systématiquement
            
            **Erreurs à éviter** :
            - Description trop vague
            - Ignorer les risques
            - Objectifs irréalistes
            - Négliger le suivi
            """
        }
    ]
    
    # Afficher les FAQs
    for faq in faqs:
        with st.expander(faq['question'], expanded=False):
            st.markdown(faq['answer'])
    
    # Section contact
    st.markdown("### 📞 Support")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div style="background: #f3f4f6; padding: 15px; border-radius: 10px;">
                <h4 style="margin: 0;">💬 Chat en direct</h4>
                <p style="margin: 10px 0 0 0;">
                    Assistance instantanée avec notre équipe
                </p>
                <button style="background: #3b82f6; color: white; border: none; 
                               padding: 10px 20px; border-radius: 5px; margin-top: 10px;">
                    Démarrer le chat
                </button>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            """
            <div style="background: #f3f4f6; padding: 15px; border-radius: 10px;">
                <h4 style="margin: 0;">📧 Email</h4>
                <p style="margin: 10px 0 0 0;">
                    support@nexora-law.ai
                </p>
                <p style="margin: 5px 0 0 0; color: #666;">
                    Réponse sous 24h
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Raccourcis clavier
    st.markdown("### ⌨️ Raccourcis clavier")
    
    shortcuts = [
        ("Ctrl/Cmd + S", "Sauvegarder la stratégie"),
        ("Ctrl/Cmd + E", "Exporter"),
        ("Ctrl/Cmd + N", "Nouvelle stratégie"),
        ("Ctrl/Cmd + F", "Rechercher"),
        ("Escape", "Fermer les dialogues")
    ]
    
    cols = st.columns(2)
    
    for i, (shortcut, action) in enumerate(shortcuts):
        with cols[i % 2]:
            st.markdown(f"**`{shortcut}`** : {action}")

# Fonctions utilitaires

def get_strategy_templates() -> Dict[str, Dict[str, Any]]:
    """Retourne les templates de stratégies disponibles"""
    return {
        'penal': {
            'name': 'Défense pénale',
            'icon': '⚖️',
            'axes': ['Contestation procédure', 'Absence d\'intention', 'Légitime défense', 'Prescription', 'Nullité des preuves'],
            'focus': 'innocence et respect de la procédure'
        },
        'commercial': {
            'name': 'Litige commercial',
            'icon': '💼',
            'axes': ['Inexécution contractuelle', 'Force majeure', 'Vice caché', 'Bonne foi', 'Clause abusive'],
            'focus': 'respect des obligations contractuelles'
        },
        'civil': {
            'name': 'Affaire civile',
            'icon': '👥',
            'axes': ['Responsabilité', 'Préjudice', 'Causalité', 'Réparation', 'Prescription'],
            'focus': 'établissement du préjudice et de la responsabilité'
        },
        'administratif': {
            'name': 'Contentieux administratif',
            'icon': '🏛️',
            'axes': ['Excès de pouvoir', 'Illégalité', 'Détournement', 'Incompétence', 'Vice de forme'],
            'focus': 'légalité des décisions administratives'
        },
        'social': {
            'name': 'Droit social',
            'icon': '👔',
            'axes': ['Licenciement abusif', 'Harcèlement', 'Discrimination', 'Heures supplémentaires', 'Accident du travail'],
            'focus': 'protection des droits du salarié'
        },
        'family': {
            'name': 'Droit de la famille',
            'icon': '👨‍👩‍👧‍👦',
            'axes': ['Garde des enfants', 'Pension alimentaire', 'Partage des biens', 'Violence conjugale', 'Adoption'],
            'focus': 'intérêt supérieur de l\'enfant et équité'
        }
    }

def generate_main_approach(config: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """Génère l'approche stratégique principale"""
    
    # Sélectionner les axes selon le contexte
    selected_axes = []
    context_lower = config['context'].lower()
    
    # Analyse intelligente du contexte
    keyword_axes = {
        'procédure': template['axes'][0],
        'intention': template['axes'][1] if len(template['axes']) > 1 else None,
        'défense': template['axes'][2] if len(template['axes']) > 2 else None,
        'prescription': 'Prescription',
        'preuve': 'Contestation des preuves',
        'bonne foi': 'Bonne foi',
        'force majeure': 'Force majeure'
    }
    
    for keyword, axis in keyword_axes.items():
        if keyword in context_lower and axis:
            if axis in template['axes']:
                selected_axes.append(axis)
    
    # Si pas assez d'axes, prendre les premiers du template
    if len(selected_axes) < 2:
        for axis in template['axes']:
            if axis not in selected_axes:
                selected_axes.append(axis)
            if len(selected_axes) >= 3:
                break
    
    # Générer le narrative selon la complexité
    complexity_narratives = {
        '🟢 Simple': "approche directe et efficace",
        '🟡 Modérée': "stratégie équilibrée et méthodique",
        '🟠 Complexe': "défense sophistiquée et multi-angles",
        '🔴 Très complexe': "stratégie approfondie et exhaustive"
    }
    
    narrative = f"""La défense s'articulera autour de {len(selected_axes)} axes stratégiques majeurs, 
    adoptant une {complexity_narratives.get(config['complexity'], 'approche adaptée')}. 
    L'accent sera mis sur {template['focus']}, avec une attention particulière aux éléments 
    favorables identifiés. Cette stratégie vise prioritairement à {config['objectives'][0].lower()}, 
    tout en préservant les options de négociation et d'appel."""
    
    # Message clé adapté
    key_messages = {
        'penal': "Notre client a agi dans le strict respect de la loi et ses droits fondamentaux ont été bafoués.",
        'commercial': "Les obligations contractuelles ont été scrupuleusement respectées par notre client.",
        'civil': "Aucune responsabilité ne peut être imputée à notre client dans cette affaire.",
        'administratif': "La décision administrative contestée est entachée d'illégalité manifeste.",
        'social': "Les droits fondamentaux de notre client ont été gravement méconnus.",
        'family': "L'intérêt supérieur de l'enfant commande la solution que nous préconisons."
    }
    
    return {
        'title': f"Stratégie de {template['name']} - Approche {config['urgency'].split()[1]}",
        'focus': template['focus'],
        'primary_axes': selected_axes[:3],
        'narrative': narrative,
        'key_message': key_messages.get(config['case_type'], 
                                       "Notre client a agi de bonne foi dans le respect de ses obligations."),
        'strategic_advantages': [
            "Position juridique solide sur les points essentiels",
            "Arguments factuels étayés par des preuves tangibles",
            "Précédents jurisprudentiels favorables identifiés"
        ]
    }

def generate_action_plan(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Génère un plan d'action détaillé et réaliste"""
    
    actions = []
    
    # Phase immédiate pour les cas urgents/critiques
    if config['urgency'] in ['🟠 Élevée', '🔴 Critique']:
        actions.append({
            'phase': 'Phase urgente (0-72h)',
            'priority': 'Critique',
            'duration': '3 jours',
            'tasks': [
                'Constitution immédiate de l\'équipe de crise juridique',
                'Audit exhaustif et sécurisation de toutes les preuves',
                'Identification et prise de contact avec les témoins clés',
                'Analyse des délais procéduraux et actions conservatoires',
                'Première réponse stratégique aux urgences procédurales',
                'Brief client et alignement sur la stratégie d\'urgence'
            ],
            'resources': ['Avocat senior', 'Équipe de crise', 'Expert IT pour preuves numériques'],
            'deliverables': [
                'Rapport d\'urgence',
                'Plan d\'action immédiat',
                'Mesures conservatoires déposées'
            ]
        })
    
    # Phase d'analyse approfondie
    actions.append({
        'phase': 'Phase d\'analyse (Semaine 1-2)',
        'priority': 'Élevée',
        'duration': '2 semaines',
        'tasks': [
            'Analyse juridique exhaustive du dossier',
            'Recherche jurisprudentielle approfondie',
            'Cartographie des arguments adverses potentiels',
            'Évaluation détaillée des forces et faiblesses',
            'Identification des experts nécessaires',
            'Stratégie de communication (si médiatisé)'
        ],
        'resources': ['Équipe juridique complète', 'Documentaliste juridique'],
        'deliverables': [
            'Mémorandum juridique complet',
            'Rapport de jurisprudence',
            'Matrice SWOT détaillée'
        ]
    })
    
    # Phase de construction
    actions.append({
        'phase': 'Phase de construction (Semaine 3-6)',
        'priority': 'Normale',
        'duration': '4 semaines',
        'tasks': [
            'Développement des arguments principaux et subsidiaires',
            'Préparation des pièces et organisation du dossier',
            'Rédaction des premières conclusions',
            'Coordination avec les experts (si applicable)',
            'Préparation des témoins',
            'Élaboration de la stratégie de négociation'
        ],
        'resources': ['Avocat plaidant', 'Assistants juridiques', 'Experts'],
        'deliverables': [
            'Projet de conclusions',
            'Dossier de pièces organisé',
            'Rapports d\'expertise'
        ]
    })
    
    # Phase de finalisation
    actions.append({
        'phase': 'Phase de finalisation (Semaine 7-8)',
        'priority': 'Normale',
        'duration': '2 semaines',
        'tasks': [
            'Finalisation et dépôt des conclusions',
            'Préparation intensive de la plaidoirie',
            'Simulations et moot courts',
            'Anticipation des questions du tribunal',
            'Derniers ajustements stratégiques',
            'Brief final avec le client'
        ],
        'resources': ['Équipe de plaidoirie', 'Coach en communication'],
        'deliverables': [
            'Conclusions définitives déposées',
            'Dossier de plaidoirie',
            'Éléments visuels (si pertinent)'
        ]
    })
    
    # Phase de suivi (toujours incluse)
    actions.append({
        'phase': 'Phase de suivi post-audience',
        'priority': 'Stratégique',
        'duration': 'Variable',
        'tasks': [
            'Analyse du déroulement de l\'audience',
            'Notes complémentaires si sollicitées',
            'Préparation à un éventuel appel',
            'Communication avec le client',
            'Veille sur la décision',
            'Archivage et retour d\'expérience'
        ],
        'resources': ['Avocat responsable', 'Assistant'],
        'deliverables': [
            'Compte-rendu d\'audience',
            'Plan d\'appel (si nécessaire)',
            'Rapport de clôture'
        ]
    })
    
    # Adapter selon la complexité
    if config['complexity'] in ['🟠 Complexe', '🔴 Très complexe']:
        # Ajouter une phase d'expertise
        actions.insert(3, {
            'phase': 'Phase d\'expertise (Semaine 4-8)',
            'priority': 'Élevée',
            'duration': '4 semaines',
            'tasks': [
                'Sélection et briefing des experts',
                'Supervision des opérations d\'expertise',
                'Analyse des rapports préliminaires',
                'Contre-expertise si nécessaire',
                'Intégration des conclusions dans la stratégie',
                'Préparation de l\'expert pour l\'audience'
            ],
            'resources': ['Experts techniques', 'Avocat spécialisé'],
            'deliverables': [
                'Rapports d\'expertise',
                'Synthèse des conclusions',
                'Support visuel technique'
            ]
        })
    
    return actions

def generate_legal_arguments(config: Dict[str, Any]) -> Dict[str, Any]:
    """Génère des arguments juridiques structurés"""
    
    arguments = {
        'principaux': [],
        'subsidiaires': [],
        'contra': []
    }
    
    # Arguments selon le type d'affaire
    case_arguments = {
        'penal': {
            'principaux': [
                {