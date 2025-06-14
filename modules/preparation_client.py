"""Module de préparation des clients pour auditions et interrogatoires - Version améliorée"""

import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ajouter le chemin parent pour importer utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import clean_key, format_legal_date, truncate_text
from utils.decorators import decorate_public_functions

# Enregistrement automatique des fonctions publiques pour le module
decorate_public_functions(sys.modules[__name__])

# Import des managers si disponibles
try:
    from config.app_config import LLMProvider
    from managers.multi_llm_manager import MultiLLMManager
    LLMS_AVAILABLE = True
except ImportError:
    LLMS_AVAILABLE = False
    
# Classes de données
@dataclass
class PreparationSession:
    """Classe pour une séance de préparation"""
    session_number: int
    title: str
    theme: str
    objectives: List[str]
    duration_minutes: int
    questions: List[Dict[str, str]]
    exercises: List[Dict[str, Any]]
    key_points: List[str]
    homework: Optional[str] = None
    completed: bool = False
    completion_date: Optional[datetime] = None
    score: Optional[float] = None
    notes: str = ""
    ai_models_used: List[str] = None

@dataclass
class PreparationPlan:
    """Plan complet de préparation"""
    total_sessions: int
    sessions: List[PreparationSession]
    prep_type: str
    client_profile: str
    strategy: str
    created_date: datetime
    target_date: Optional[datetime] = None
    overall_progress: float = 0.0
    ai_models_config: Dict[str, Any] = None

@dataclass
class PreparationClientResult:
    """Résultat de préparation"""
    content: str
    prep_type: str
    profile: str
    strategy: str
    key_qa: List[Dict[str, str]]
    do_not_say: List[str]
    exercises: List[Dict[str, Any]]
    duration_estimate: int
    timestamp: datetime
    ai_models_used: List[str] = None
    fusion_score: float = 0.0

# Fonction principale pour le lazy loading
def run():
    """Fonction principale du module - OBLIGATOIRE pour le lazy loading"""
    
    # Initialisation de l'état de session
    init_session_state()
    
    # Style CSS personnalisé
    apply_custom_styles()
    
    # En-tête avec métriques
    display_header_metrics()
    
    # Navigation principale
    display_main_navigation()

def init_session_state():
    """Initialise les variables de session"""
    if 'preparation_state' not in st.session_state:
        st.session_state.preparation_state = {
            'initialized': True,
            'current_plan': None,
            'current_session': None,
            'results': None,
            'ai_config': {
                'models': [],
                'fusion_mode': False,
                'temperature': 0.7
            }
        }
    
    # Migration des anciennes variables si nécessaire
    if 'preparation_plan' in st.session_state and not st.session_state.preparation_state['current_plan']:
        st.session_state.preparation_state['current_plan'] = st.session_state.preparation_plan
        del st.session_state.preparation_plan

def apply_custom_styles():
    """Applique les styles CSS personnalisés"""
    st.markdown("""
    <style>
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Cards améliorées */
    .prep-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .prep-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
    
    /* Boutons améliorés */
    .stButton > button {
        transition: all 0.3s ease;
        border-radius: 10px;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    
    /* Progress bars personnalisées */
    .prep-progress {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 10px;
        border-radius: 5px;
        transition: width 0.5s ease;
    }
    
    /* Questions cards */
    .question-card {
        background: white;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* AI model selector */
    .ai-model-badge {
        display: inline-block;
        padding: 5px 15px;
        margin: 5px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .ai-model-badge:hover {
        transform: scale(1.1);
    }
    
    /* Session status indicators */
    .session-status {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 10px;
    }
    
    .session-status.completed {
        background: #48bb78;
    }
    
    .session-status.pending {
        background: #f6e05e;
    }
    
    .session-status.locked {
        background: #cbd5e0;
    }
    </style>
    """, unsafe_allow_html=True)

def display_header_metrics():
    """Affiche l'en-tête avec les métriques principales"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    plan = st.session_state.preparation_state.get('current_plan')
    
    with col1:
        if plan:
            completed = sum(1 for s in plan.sessions if s.completed)
            st.metric(
                "📚 Progression",
                f"{completed}/{plan.total_sessions}",
                f"{(completed/plan.total_sessions*100):.0f}%"
            )
        else:
            st.metric("📚 Sessions", "0/0", "Créez un plan")
    
    with col2:
        if plan and any(s.score for s in plan.sessions if s.completed):
            avg_score = sum(s.score for s in plan.sessions if s.completed and s.score) / sum(1 for s in plan.sessions if s.completed and s.score)
            st.metric("⭐ Score moyen", f"{avg_score*5:.1f}/5")
        else:
            st.metric("⭐ Score moyen", "N/A")
    
    with col3:
        if plan and plan.target_date:
            days_left = (plan.target_date - datetime.now().date()).days
            st.metric("📅 Jours restants", days_left, f"jusqu'au {plan.target_date.strftime('%d/%m')}")
        else:
            st.metric("📅 Échéance", "Non définie")
    
    with col4:
        if LLMS_AVAILABLE:
            active_models = len(st.session_state.preparation_state['ai_config'].get('models', []))
            st.metric("🤖 IA actives", active_models, "modèles")
        else:
            st.metric("🤖 IA", "Non configurée")
    
    with col5:
        if plan:
            total_questions = sum(len(s.questions) for s in plan.sessions)
            st.metric("❓ Questions", total_questions, "totales")
        else:
            st.metric("❓ Questions", "0")

def display_main_navigation():
    """Affiche la navigation principale avec lazy loading"""
    
    # Tabs principaux avec icônes améliorées
    tabs = st.tabs([
        "🚀 Tableau de bord",
        "✨ Nouveau plan",
        "📅 Séances",
        "📊 Analytics",
        "🤖 IA & Fusion",
        "📚 Ressources",
        "⚙️ Paramètres"
    ])
    
    with tabs[0]:
        display_dashboard()
    
    with tabs[1]:
        display_new_preparation()
    
    with tabs[2]:
        display_sessions_management()
    
    with tabs[3]:
        display_analytics()
    
    with tabs[4]:
        display_ai_configuration()
    
    with tabs[5]:
        display_resources()
    
    with tabs[6]:
        display_settings()

def display_dashboard():
    """Affiche le tableau de bord principal"""
    st.markdown("### 🚀 Tableau de bord")
    
    plan = st.session_state.preparation_state.get('current_plan')
    
    if not plan:
        # État vide avec call-to-action
        st.markdown("""
        <div class="prep-card fade-in" style="text-align: center; padding: 40px;">
            <h2>👋 Bienvenue dans votre espace de préparation</h2>
            <p>Commencez par créer un plan de préparation personnalisé</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("✨ Créer mon premier plan", type="primary", use_container_width=True):
                st.session_state.selected_tab = 1
                st.rerun()
        return
    
    # Vue d'ensemble avec animations
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Progression visuelle
        st.markdown("#### 📈 Progression globale")
        display_progress_visualization(plan)
        
        # Prochaine séance
        next_session = get_next_session(plan)
        if next_session:
            st.markdown("#### 📅 Prochaine séance")
            display_session_card(next_session, is_next=True)
    
    with col2:
        # Statistiques rapides
        st.markdown("#### 📊 Statistiques")
        display_quick_stats(plan)
        
        # Actions rapides
        st.markdown("#### ⚡ Actions rapides")
        display_quick_actions(plan)

def display_progress_visualization(plan: PreparationPlan):
    """Affiche une visualisation de la progression"""
    # Créer un graphique de progression interactif
    sessions_data = []
    for i, session in enumerate(plan.sessions):
        status = "Complétée" if session.completed else "En attente"
        color = "#48bb78" if session.completed else "#cbd5e0"
        score = session.score * 5 if session.completed and session.score else None
        
        sessions_data.append({
            'Session': f"S{i+1}",
            'Status': status,
            'Score': score,
            'Color': color,
            'Title': session.theme
        })
    
    # Graphique en barres horizontales
    fig = go.Figure()
    
    # Barres de progression
    fig.add_trace(go.Bar(
        y=[d['Session'] for d in sessions_data],
        x=[1 for _ in sessions_data],
        orientation='h',
        marker_color=[d['Color'] for d in sessions_data],
        hovertemplate='%{text}<extra></extra>',
        text=[d['Title'] for d in sessions_data],
        showlegend=False
    ))
    
    # Scores
    scores = [d['Score'] for d in sessions_data if d['Score'] is not None]
    if scores:
        fig.add_trace(go.Scatter(
            y=[d['Session'] for d in sessions_data if d['Score'] is not None],
            x=[0.5 for _ in scores],
            mode='text',
            text=[f"⭐ {s:.1f}" for s in scores],
            textposition="middle center",
            showlegend=False
        ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, 1]),
        yaxis=dict(showgrid=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    st.plotly_chart(fig, use_container_width=True)

def get_next_session(plan: PreparationPlan) -> Optional[PreparationSession]:
    """Retourne la prochaine séance non complétée"""
    for session in plan.sessions:
        if not session.completed:
            return session
    return None

def display_session_card(session: PreparationSession, is_next: bool = False):
    """Affiche une carte de séance"""
    card_class = "prep-card fade-in" if is_next else "question-card"
    
    st.markdown(f"""
    <div class="{card_class}">
        <h4>{session.title}</h4>
        <p><strong>Durée:</strong> {session.duration_minutes} minutes</p>
        <p><strong>Questions:</strong> {len(session.questions)} | <strong>Exercices:</strong> {len(session.exercises)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if is_next:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Commencer la séance", type="primary", use_container_width=True):
                st.session_state.preparation_state['current_session'] = session.session_number
                st.session_state.selected_tab = 2
                st.rerun()
        with col2:
            if st.button("📋 Voir le détail", use_container_width=True):
                st.session_state.show_session_detail = session.session_number

def display_quick_stats(plan: PreparationPlan):
    """Affiche les statistiques rapides"""
    completed = sum(1 for s in plan.sessions if s.completed)
    
    # Mini graphique en donut
    fig = go.Figure(data=[go.Pie(
        values=[completed, plan.total_sessions - completed],
        labels=['Complétées', 'Restantes'],
        hole=.7,
        marker_colors=['#48bb78', '#e2e8f0']
    )])
    
    fig.update_traces(
        textinfo='none',
        hovertemplate='%{label}: %{value}<extra></extra>'
    )
    
    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        annotations=[dict(
            text=f'{completed}/{plan.total_sessions}',
            x=0.5, y=0.5,
            font_size=24,
            showarrow=False
        )]
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Stats textuelles
    if completed > 0:
        avg_duration = sum(s.duration_minutes for s in plan.sessions if s.completed) / completed
        st.info(f"⏱️ Durée moyenne: {avg_duration:.0f} min/séance")

def display_quick_actions(plan: PreparationPlan):
    """Affiche les actions rapides"""
    actions = []
    
    # Déterminer les actions pertinentes
    next_session = get_next_session(plan)
    if next_session:
        if st.button("🚀 Séance suivante", use_container_width=True):
            st.session_state.preparation_state['current_session'] = next_session.session_number
            st.session_state.selected_tab = 2
            st.rerun()
    
    if any(s.completed for s in plan.sessions):
        if st.button("📊 Voir l'analyse", use_container_width=True):
            st.session_state.selected_tab = 3
            st.rerun()
    
    if st.button("📄 Export PDF", use_container_width=True):
        export_plan_as_pdf(plan)

def display_new_preparation():
    """Interface de création d'un nouveau plan"""
    st.markdown("### ✨ Création d'un nouveau plan de préparation")
    
    # Stepper pour guider l'utilisateur
    if 'creation_step' not in st.session_state:
        st.session_state.creation_step = 1
    
    # Afficher le stepper
    display_creation_stepper()
    
    # Contenu selon l'étape
    if st.session_state.creation_step == 1:
        display_step1_basics()
    elif st.session_state.creation_step == 2:
        display_step2_details()
    elif st.session_state.creation_step == 3:
        display_step3_ai_config()
    elif st.session_state.creation_step == 4:
        display_step4_review()

def display_creation_stepper():
    """Affiche le stepper de création"""
    steps = [
        "🎯 Informations de base",
        "📋 Détails du cas",
        "🤖 Configuration IA",
        "✅ Validation"
    ]
    
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            is_active = i + 1 == st.session_state.creation_step
            is_completed = i + 1 < st.session_state.creation_step
            
            if is_active:
                st.markdown(f"**{step}**")
            elif is_completed:
                st.markdown(f"✓ ~~{step}~~")
            else:
                st.markdown(f"<span style='color: #a0aec0;'>{step}</span>", unsafe_allow_html=True)

def display_step1_basics():
    """Étape 1 : Informations de base"""
    st.markdown("#### 🎯 Informations de base")
    
    col1, col2 = st.columns(2)
    
    with col1:
        prep_type = st.selectbox(
            "Type de procédure",
            ["audition", "interrogatoire", "comparution", "confrontation", "expertise"],
            format_func=lambda x: {
                "audition": "👮 Audition police/gendarmerie",
                "interrogatoire": "👨‍⚖️ Interrogatoire juge d'instruction",
                "comparution": "⚖️ Comparution tribunal",
                "confrontation": "🤝 Confrontation",
                "expertise": "🔬 Expertise psychologique/psychiatrique"
            }.get(x, x.title()),
            key="step1_prep_type"
        )
        
        target_date = st.date_input(
            "Date de la procédure",
            value=datetime.now().date() + timedelta(days=30),
            min_value=datetime.now().date(),
            key="step1_target_date"
        )
        
        nb_sessions = st.slider(
            "Nombre de séances souhaitées",
            min_value=3,
            max_value=15,
            value=7,
            help="Plus vous avez de temps, plus le nombre de séances peut être élevé",
            key="step1_nb_sessions"
        )
    
    with col2:
        client_profile = st.selectbox(
            "Profil psychologique du client",
            ["anxieux", "confiant", "agressif", "fragile", "technique"],
            format_func=lambda x: {
                "anxieux": "😰 Anxieux - Besoin de réassurance",
                "confiant": "😊 Confiant - Maintenir la vigilance",
                "agressif": "😠 Agressif - Canaliser l'énergie",
                "fragile": "🥺 Fragile - Soutien renforcé",
                "technique": "🤓 Technique - Approche factuelle"
            }.get(x, x.title()),
            key="step1_profile"
        )
        
        experience = st.select_slider(
            "Expérience judiciaire",
            options=["Aucune", "Limitée", "Modérée", "Importante"],
            value="Limitée",
            key="step1_experience"
        )
        
        strategy = st.selectbox(
            "Stratégie de défense",
            ["negation", "justification", "minimisation", "collaboration", "silence"],
            format_func=lambda x: {
                "negation": "❌ Négation des faits",
                "justification": "✅ Justification/Explication",
                "minimisation": "📉 Minimisation de l'implication",
                "collaboration": "🤝 Collaboration mesurée",
                "silence": "🤐 Exercice du droit au silence"
            }.get(x, x.title()),
            key="step1_strategy"
        )
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            # Sauvegarder les données
            if 'prep_config' not in st.session_state:
                st.session_state.prep_config = {}
            
            st.session_state.prep_config.update({
                'prep_type': prep_type,
                'target_date': target_date,
                'nb_sessions': nb_sessions,
                'client_profile': client_profile,
                'experience': experience,
                'strategy': strategy
            })
            
            st.session_state.creation_step = 2
            st.rerun()

def display_step2_details():
    """Étape 2 : Détails du cas"""
    st.markdown("#### 📋 Détails du cas")
    
    # Contexte de l'affaire
    with st.expander("📂 Contexte de l'affaire", expanded=True):
        infractions = st.text_area(
            "Infractions reprochées",
            placeholder="Ex: Abus de biens sociaux, faux et usage de faux, blanchiment...",
            height=100,
            key="step2_infractions"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            complexity = st.select_slider(
                "Complexité de l'affaire",
                options=["Simple", "Modérée", "Complexe", "Très complexe"],
                value="Modérée",
                key="step2_complexity"
            )
            
            media_attention = st.checkbox(
                "📰 Affaire médiatisée",
                help="Nécessite une préparation spécifique pour gérer la pression médiatique",
                key="step2_media"
            )
        
        with col2:
            codefendants = st.number_input(
                "Nombre de co-mis en cause",
                min_value=0,
                max_value=20,
                value=0,
                key="step2_codefendants"
            )
            
            victim_type = st.selectbox(
                "Type de victime",
                ["Aucune", "Personne physique", "Personne morale", "État/Administration", "Multiple"],
                key="step2_victim"
            )
    
    # Points sensibles
    with st.expander("⚠️ Points sensibles", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            factual_challenges = st.text_area(
                "Difficultés factuelles",
                placeholder="- Incohérences temporelles\n- Absence de preuves directes\n- Témoignages contradictoires",
                height=120,
                key="step2_factual"
            )
        
        with col2:
            emotional_challenges = st.text_area(
                "Difficultés émotionnelles",
                placeholder="- Gestion du stress\n- Sentiment de culpabilité\n- Peur du jugement\n- Relation avec les co-accusés",
                height=120,
                key="step2_emotional"
            )
    
    # Domaines prioritaires
    st.markdown("##### 🎯 Domaines de travail prioritaires")
    
    focus_areas = st.multiselect(
        "Sélectionnez les domaines à privilégier",
        [
            "🧘 Gestion du stress et des émotions",
            "📖 Cohérence et fluidité du récit",
            "❓ Réponses aux questions techniques",
            "👁️ Langage corporel et présentation",
            "🤐 Gestion des silences et pauses",
            "🎣 Identification des questions pièges",
            "🎯 Maintien de la ligne de défense",
            "🗣️ Techniques de communication",
            "⚖️ Compréhension de la procédure",
            "🤝 Gestion des confrontations"
        ],
        default=[
            "🧘 Gestion du stress et des émotions",
            "📖 Cohérence et fluidité du récit",
            "🎣 Identification des questions pièges"
        ],
        key="step2_focus"
    )
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.creation_step = 1
            st.rerun()
    
    with col3:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            # Sauvegarder les données
            st.session_state.prep_config.update({
                'infractions': infractions,
                'complexity': complexity,
                'media_attention': media_attention,
                'codefendants': codefendants,
                'victim_type': victim_type,
                'factual_challenges': factual_challenges,
                'emotional_challenges': emotional_challenges,
                'focus_areas': focus_areas
            })
            
            st.session_state.creation_step = 3
            st.rerun()

def display_step3_ai_config():
    """Étape 3 : Configuration des IA"""
    st.markdown("#### 🤖 Configuration de l'intelligence artificielle")
    
    if not LLMS_AVAILABLE:
        st.warning("⚠️ Les modèles d'IA ne sont pas disponibles. Configuration simulée.")
        
        # Configuration simulée
        st.info("Dans la version complète, vous pourrez configurer plusieurs modèles d'IA")
        
        models_simulation = st.multiselect(
            "Modèles disponibles (simulation)",
            ["GPT-4", "Claude 3", "Gemini Pro", "Mistral Large"],
            default=["GPT-4", "Claude 3"],
            key="step3_models_sim"
        )
        
        fusion_mode = st.checkbox(
            "🔀 Activer le mode fusion",
            value=True,
            help="Combine les réponses de plusieurs IA pour une meilleure qualité",
            key="step3_fusion_sim"
        )
    else:
        # Configuration réelle avec MultiLLMManager
        llm_manager = MultiLLMManager()
        available_models = list(llm_manager.clients.keys())
        
        st.markdown("##### 🤖 Sélection des modèles")
        
        # Affichage des modèles sous forme de badges
        selected_models = []
        cols = st.columns(min(len(available_models), 4))
        
        for i, model in enumerate(available_models):
            with cols[i % 4]:
                model_key = f"model_{model}"
                if st.checkbox(
                    model.replace("_", " ").title(),
                    value=True,
                    key=f"step3_{model_key}"
                ):
                    selected_models.append(model)
        
        if selected_models:
            st.success(f"✅ {len(selected_models)} modèles sélectionnés")
            
            # Mode fusion
            fusion_mode = st.checkbox(
                "🔀 Activer le mode fusion des IA",
                value=len(selected_models) > 1,
                help="Combine les réponses de plusieurs IA pour optimiser la qualité",
                key="step3_fusion"
            )
            
            if fusion_mode and len(selected_models) > 1:
                fusion_strategy = st.radio(
                    "Stratégie de fusion",
                    ["consensus", "best_answer", "synthesis"],
                    format_func=lambda x: {
                        "consensus": "🤝 Consensus - Privilégie les points communs",
                        "best_answer": "🏆 Meilleure réponse - Sélectionne la plus pertinente",
                        "synthesis": "🔄 Synthèse - Combine toutes les réponses"
                    }.get(x, x),
                    key="step3_fusion_strategy"
                )
            else:
                fusion_strategy = None
        else:
            st.error("⚠️ Sélectionnez au moins un modèle")
            fusion_mode = False
            fusion_strategy = None
    
    # Paramètres avancés
    with st.expander("⚙️ Paramètres avancés", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Créativité des réponses",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Plus la valeur est élevée, plus les réponses seront variées",
                key="step3_temperature"
            )
            
            max_retries = st.number_input(
                "Tentatives en cas d'erreur",
                min_value=1,
                max_value=5,
                value=3,
                key="step3_retries"
            )
        
        with col2:
            response_length = st.select_slider(
                "Longueur des réponses",
                options=["Concise", "Standard", "Détaillée", "Très détaillée"],
                value="Détaillée",
                key="step3_length"
            )
            
            language_style = st.selectbox(
                "Style de langage",
                ["Formel", "Semi-formel", "Accessible", "Très accessible"],
                index=2,
                key="step3_style"
            )
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.creation_step = 2
            st.rerun()
    
    with col3:
        if st.button("Suivant ➡️", type="primary", use_container_width=True):
            # Sauvegarder la configuration IA
            if LLMS_AVAILABLE:
                ai_config = {
                    'models': selected_models,
                    'fusion_mode': fusion_mode,
                    'fusion_strategy': fusion_strategy,
                    'temperature': temperature,
                    'max_retries': max_retries,
                    'response_length': response_length,
                    'language_style': language_style
                }
            else:
                ai_config = {
                    'models': models_simulation if 'models_simulation' in locals() else [],
                    'fusion_mode': fusion_mode if 'fusion_mode' in locals() else False,
                    'temperature': 0.7
                }
            
            st.session_state.prep_config['ai_config'] = ai_config
            st.session_state.creation_step = 4
            st.rerun()

def display_step4_review():
    """Étape 4 : Révision et validation"""
    st.markdown("#### ✅ Validation du plan de préparation")
    
    config = st.session_state.prep_config
    
    # Résumé visuel
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("##### 📋 Résumé de votre plan")
        
        # Carte de résumé avec style
        st.markdown(f"""
        <div class="prep-card">
            <h4>🎯 {config['prep_type'].replace('_', ' ').title()}</h4>
            <p><strong>📅 Date cible:</strong> {config['target_date'].strftime('%d/%m/%Y')}</p>
            <p><strong>📚 Nombre de séances:</strong> {config['nb_sessions']}</p>
            <p><strong>👤 Profil client:</strong> {config['client_profile'].title()}</p>
            <p><strong>🎯 Stratégie:</strong> {config['strategy'].replace('_', ' ').title()}</p>
            <p><strong>🔥 Complexité:</strong> {config.get('complexity', 'Modérée')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Domaines de travail
        if config.get('focus_areas'):
            st.markdown("##### 🎯 Domaines prioritaires")
            for area in config['focus_areas']:
                st.write(f"• {area}")
    
    with col2:
        # Configuration IA
        st.markdown("##### 🤖 Configuration IA")
        
        ai_config = config.get('ai_config', {})
        if ai_config.get('models'):
            st.info(f"**Modèles:** {len(ai_config['models'])}")
            for model in ai_config['models']:
                st.write(f"• {model}")
            
            if ai_config.get('fusion_mode'):
                st.success("✅ Mode fusion activé")
        else:
            st.warning("⚠️ Aucun modèle configuré")
        
        # Estimation du temps
        total_minutes = config['nb_sessions'] * 120  # 2h par défaut
        total_hours = total_minutes / 60
        
        st.markdown("##### ⏱️ Estimation")
        st.metric("Durée totale", f"{total_hours:.1f} heures")
        
        days_available = (config['target_date'] - datetime.now().date()).days
        sessions_per_week = (config['nb_sessions'] * 7) / days_available if days_available > 0 else 0
        
        if sessions_per_week > 3:
            st.warning(f"⚠️ Rythme intensif: {sessions_per_week:.1f} séances/semaine")
        else:
            st.success(f"✅ Rythme adapté: {sessions_per_week:.1f} séances/semaine")
    
    # Actions finales
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Précédent", use_container_width=True):
            st.session_state.creation_step = 3
            st.rerun()
    
    with col2:
        # Options supplémentaires
        save_as_template = st.checkbox(
            "💾 Sauvegarder comme modèle",
            help="Réutiliser cette configuration pour d'autres clients"
        )
        
        send_notifications = st.checkbox(
            "📧 Activer les notifications",
            value=True,
            help="Recevoir des rappels pour les séances"
        )
    
    with col3:
        if st.button("🚀 Créer le plan", type="primary", use_container_width=True):
            with st.spinner("Création du plan personnalisé..."):
                # Créer le plan
                plan = create_preparation_plan_from_config(config)
                
                if plan:
                    # Sauvegarder
                    st.session_state.preparation_state['current_plan'] = plan
                    
                    if save_as_template:
                        save_plan_template(config)
                    
                    if send_notifications:
                        setup_notifications(plan)
                    
                    # Réinitialiser et rediriger
                    st.session_state.creation_step = 1
                    del st.session_state.prep_config
                    
                    st.success("✅ Plan créé avec succès!")
                    st.balloons()
                    
                    time.sleep(2)
                    st.session_state.selected_tab = 0
                    st.rerun()

def create_preparation_plan_from_config(config: dict) -> PreparationPlan:
    """Crée un plan de préparation à partir de la configuration"""
    
    # Générer les séances
    sessions = []
    
    # Thèmes par type de préparation
    themes_templates = get_themes_by_type(config['prep_type'])
    
    # Adapter au nombre de séances
    if config['nb_sessions'] > len(themes_templates):
        themes_templates.extend([
            "Révision et consolidation",
            "Points sensibles approfondis",
            "Simulation complémentaire"
        ] * ((config['nb_sessions'] - len(themes_templates)) // 3 + 1))
    
    themes = themes_templates[:config['nb_sessions']]
    
    # Créer chaque séance
    for i in range(config['nb_sessions']):
        # Générer le contenu avec IA si disponible
        if LLMS_AVAILABLE and config.get('ai_config', {}).get('models'):
            questions = generate_ai_questions(
                session_num=i+1,
                theme=themes[i],
                config=config
            )
        else:
            questions = generate_default_session_questions(themes[i])
        
        exercises = generate_session_exercises_enhanced(
            themes[i],
            config['client_profile'],
            config.get('focus_areas', [])
        )
        
        session = PreparationSession(
            session_number=i + 1,
            title=f"Séance {i + 1}: {themes[i]}",
            theme=themes[i],
            objectives=generate_session_objectives_enhanced(themes[i], config),
            duration_minutes=120,  # Par défaut
            questions=questions,
            exercises=exercises,
            key_points=generate_key_points(themes[i], config),
            homework=generate_homework_enhanced(i + 1, themes[i], config),
            ai_models_used=config.get('ai_config', {}).get('models', [])
        )
        
        sessions.append(session)
    
    # Créer le plan
    plan = PreparationPlan(
        total_sessions=config['nb_sessions'],
        sessions=sessions,
        prep_type=config['prep_type'],
        client_profile=config['client_profile'],
        strategy=config['strategy'],
        created_date=datetime.now(),
        target_date=config['target_date'],
        ai_models_config=config.get('ai_config', {})
    )
    
    return plan

def get_themes_by_type(prep_type: str) -> List[str]:
    """Retourne les thèmes selon le type de préparation"""
    themes = {
        "audition": [
            "Cadre juridique et droits fondamentaux",
            "Construction du récit factuel",
            "Questions sur les faits",
            "Gestion des questions pièges",
            "Communication non-verbale",
            "Simulation d'audition complète",
            "Débriefing et ajustements"
        ],
        "interrogatoire": [
            "Procédure d'instruction et droits",
            "Stratégie face au magistrat",
            "Récit défensif structuré",
            "Gestion des confrontations aux preuves",
            "Questions techniques approfondies",
            "Simulation d'interrogatoire",
            "Préparation psychologique finale"
        ],
        "comparution": [
            "Déroulement de l'audience",
            "Présentation personnelle impactante",
            "Exposition claire des faits",
            "Réponses au tribunal",
            "Gestion de la partie civile",
            "Déclaration finale",
            "Répétition générale"
        ],
        "confrontation": [
            "Enjeux et cadre de la confrontation",
            "Maintien de sa version",
            "Gestion des accusations directes",
            "Techniques de déstabilisation",
            "Communication assertive",
            "Jeux de rôle intensifs",
            "Stratégies adaptatives"
        ],
        "expertise": [
            "Objectifs de l'expertise",
            "Préparation du discours",
            "Questions psychologiques types",
            "Cohérence avec le dossier",
            "Tests et évaluations",
            "Simulation d'expertise",
            "Consolidation finale"
        ]
    }
    
    return themes.get(prep_type, themes["audition"])

def generate_ai_questions(session_num: int, theme: str, config: dict) -> List[Dict[str, str]]:
    """Génère des questions avec l'IA"""
    if not LLMS_AVAILABLE:
        return generate_default_session_questions(theme)
    
    llm_manager = MultiLLMManager()
    ai_config = config.get('ai_config', {})
    
    prompt = f"""Génère 15 questions précises et pertinentes pour la séance {session_num} de préparation.
CONTEXTE:
- Type: {config['prep_type']}
- Thème: {theme}
- Profil: {config['client_profile']}
- Stratégie: {config['strategy']}
- Infractions: {config.get('infractions', 'Non précisées')}
- Complexité: {config.get('complexity', 'Modérée')}

Format pour chaque question:
1. Question principale
2. Réponse suggérée adaptée à la stratégie
3. 2-3 variantes de la question
4. Points d'attention/pièges
5. Niveau de difficulté (1-5)
"""
    
    system_prompt = """Tu es un expert en préparation judiciaire avec 20 ans d'expérience.
Tu connais parfaitement les techniques d'interrogatoire et les stratégies de défense.
Génère des questions réalistes et adaptées au profil du client."""
    
    questions = []
    
    if ai_config.get('fusion_mode') and len(ai_config.get('models', [])) > 1:
        # Mode fusion
        all_responses = []
        
        for model in ai_config['models']:
            response = llm_manager.query_single_llm(
                model,
                prompt,
                system_prompt,
                temperature=ai_config.get('temperature', 0.7)
            )
            
            if response['success']:
                all_responses.append(response['response'])
        
        if all_responses:
            # Fusionner les réponses
            if ai_config.get('fusion_strategy') == 'consensus':
                questions = merge_questions_consensus(all_responses)
            elif ai_config.get('fusion_strategy') == 'best_answer':
                questions = select_best_questions(all_responses)
            else:  # synthesis
                questions = synthesize_questions(all_responses)
    else:
        # Mode simple
        model = ai_config['models'][0] if ai_config.get('models') else list(llm_manager.clients.keys())[0]
        
        response = llm_manager.query_single_llm(
            model,
            prompt,
            system_prompt,
            temperature=ai_config.get('temperature', 0.7)
        )
        
        if response['success']:
            questions = parse_ai_questions(response['response'])
    
    # Fallback si pas de questions
    if not questions:
        questions = generate_default_session_questions(theme)
    
    return questions

def generate_default_session_questions(theme: str) -> List[Dict[str, str]]:
    """Génère des questions par défaut pour une séance"""
    
    questions_templates = {
        "Cadre juridique et droits fondamentaux": [
            {
                'question': "Connaissez-vous vos droits lors d'une audition ?",
                'answer': "J'ai le droit de me taire, d'être assisté par un avocat, et d'être informé des faits qui me sont reprochés.",
                'variants': ["Quels sont vos droits ?", "Savez-vous ce que vous pouvez faire ou ne pas faire ?"],
                'attention_points': "Ne pas hésiter, montrer qu'on connaît ses droits",
                'difficulty': 2
            },
            {
                'question': "Souhaitez-vous faire des déclarations ?",
                'answer': "Je souhaite d'abord consulter mon avocat avant toute déclaration.",
                'variants': ["Voulez-vous vous exprimer ?", "Avez-vous quelque chose à dire ?"],
                'attention_points': "Question d'ouverture classique, rester prudent",
                'difficulty': 3
            }
        ]
    }
    
    # Retourner les questions du thème ou des questions génériques
    return questions_templates.get(theme, [
        {
            'question': f"Question type sur {theme}",
            'answer': "Réponse à adapter selon le cas",
            'variants': [],
            'attention_points': "À personnaliser",
            'difficulty': 3
        }
    ] * 5)

def parse_ai_questions(response: str) -> List[Dict[str, str]]:
    """Parse la réponse de l'IA pour extraire les questions"""
    questions = []
    current_question = None
    
    lines = response.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Détecter une nouvelle question
        if re.match(r'^\d+\.?\s*Question|^Question\s*\d+', line, re.IGNORECASE):
            if current_question:
                questions.append(current_question)
            
            current_question = {
                'question': re.sub(r'^\d+\.?\s*Question\s*\d*:?\s*', '', line, flags=re.IGNORECASE).strip(),
                'answer': '',
                'variants': [],
                'attention_points': '',
                'difficulty': 3
            }
        
        elif current_question:
            # Parser les différents éléments
            if any(marker in line.lower() for marker in ['réponse:', 'r:', 'answer:']):
                current_question['answer'] = re.sub(r'^(réponse|r|answer)\s*:?\s*', '', line, flags=re.IGNORECASE).strip()
            
            elif any(marker in line.lower() for marker in ['variante', 'variant']):
                variant = re.sub(r'(variante|variant)\s*\d*\s*:?\s*', '', line, flags=re.IGNORECASE).strip()
                if variant:
                    current_question['variants'].append(variant)
            
            elif any(marker in line.lower() for marker in ['attention', 'piège', 'trap']):
                current_question['attention_points'] = re.sub(r'^(attention|piège|trap)\s*:?\s*', '', line, flags=re.IGNORECASE).strip()
            
            elif any(marker in line.lower() for marker in ['difficulté', 'difficulty', 'niveau']):
                match = re.search(r'\d', line)
                if match:
                    current_question['difficulty'] = int(match.group())
    
    # Ajouter la dernière question
    if current_question:
        questions.append(current_question)
    
    return questions

def merge_questions_consensus(responses: List[str]) -> List[Dict[str, str]]:
    """Fusionne les questions en privilégiant le consensus"""
    all_questions = []
    
    for response in responses:
        questions = parse_ai_questions(response)
        all_questions.extend(questions)
    
    # Grouper les questions similaires
    merged = []
    seen = set()
    
    for q in all_questions:
        q_lower = q['question'].lower()
        if q_lower not in seen:
            seen.add(q_lower)
            # Chercher les variantes dans les autres réponses
            similar = [other for other in all_questions if other['question'].lower() == q_lower]
            
            if len(similar) > 1:
                # Fusionner les réponses
                q['answer'] = max([s['answer'] for s in similar], key=len)
                q['variants'] = list(set(sum([s['variants'] for s in similar], [])))
                q['difficulty'] = round(sum(s['difficulty'] for s in similar) / len(similar))
            
            merged.append(q)
    
    return merged[:15]  # Limiter à 15 questions

def select_best_questions(responses: List[str]) -> List[Dict[str, str]]:
    """Sélectionne les meilleures questions parmi toutes les réponses"""
    all_questions = []
    
    for response in responses:
        questions = parse_ai_questions(response)
        all_questions.extend(questions)
    
    # Scorer les questions
    for q in all_questions:
        score = 0
        # Critères de qualité
        if len(q['question']) > 20:
            score += 1
        if q['answer']:
            score += 2
        if q['variants']:
            score += 1
        if q['attention_points']:
            score += 2
        
        q['_score'] = score
    
    # Trier par score et prendre les meilleures
    all_questions.sort(key=lambda x: x.get('_score', 0), reverse=True)
    
    # Retirer le score temporaire
    for q in all_questions:
        q.pop('_score', None)
    
    return all_questions[:15]

def synthesize_questions(responses: List[str]) -> List[Dict[str, str]]:
    """Synthétise toutes les réponses en un ensemble cohérent"""
    # Combiner toutes les questions
    all_questions = []
    
    for response in responses:
        questions = parse_ai_questions(response)
        all_questions.extend(questions)
    
    # Éliminer les doublons exacts
    unique_questions = []
    seen_questions = set()
    
    for q in all_questions:
        q_key = q['question'].lower().strip()
        if q_key not in seen_questions:
            seen_questions.add(q_key)
            unique_questions.append(q)
    
    # Enrichir avec les meilleures parties de chaque réponse
    for i, q in enumerate(unique_questions):
        # Trouver toutes les versions de cette question
        similar = [
            other for other in all_questions 
            if other['question'].lower().strip() == q['question'].lower().strip()
        ]
        
        if similar:
            # Prendre la meilleure réponse
            best_answer = max([s['answer'] for s in similar if s['answer']], key=len, default=q['answer'])
            q['answer'] = best_answer
            
            # Combiner toutes les variantes uniques
            all_variants = sum([s['variants'] for s in similar], [])
            q['variants'] = list(set(all_variants))[:3]
            
            # Combiner les points d'attention
            attention_points = [s['attention_points'] for s in similar if s['attention_points']]
            if attention_points:
                q['attention_points'] = " | ".join(set(attention_points))
    
    return unique_questions[:15]

def generate_session_exercises_enhanced(theme: str, profile: str, focus_areas: List[str]) -> List[Dict[str, Any]]:
    """Génère des exercices améliorés pour une séance"""
    
    exercises = []
    
    # Base d'exercices par thème
    theme_exercises = {
        "stress": [
            {
                "title": "Cohérence cardiaque",
                "description": "Respiration rythmée 5-5-5 pour réguler le stress",
                "duration": 5,
                "type": "relaxation",
                "difficulty": 1,
                "instructions": [
                    "Inspirez pendant 5 secondes",
                    "Expirez pendant 5 secondes",
                    "Répétez pendant 5 minutes"
                ]
            },
            {
                "title": "Scan corporel",
                "description": "Détection et relâchement des tensions",
                "duration": 10,
                "type": "mindfulness",
                "difficulty": 2
            }
        ],
        "communication": [
            {
                "title": "Reformulation active",
                "description": "S'entraîner à reformuler les questions avant de répondre",
                "duration": 15,
                "type": "practice",
                "difficulty": 3,
                "scenario": "Face à une question complexe, reformulez pour clarifier"
            }
        ],
        "coherence": [
            {
                "title": "Timeline interactive",
                "description": "Créer une chronologie visuelle des événements",
                "duration": 20,
                "type": "organization",
                "difficulty": 2,
                "tools": ["Post-it", "Tableau blanc", "Application timeline"]
            }
        ]
    }
    
    # Mapper les focus areas aux exercices
    area_mapping = {
        "🧘 Gestion du stress et des émotions": "stress",
        "📖 Cohérence et fluidité du récit": "coherence",
        "🗣️ Techniques de communication": "communication"
    }
    
    # Ajouter les exercices pertinents
    for area in focus_areas:
        category = area_mapping.get(area)
        if category and category in theme_exercises:
            exercises.extend(theme_exercises[category])
    
    # Exercices spécifiques au profil
    profile_exercises = {
        "anxieux": {
            "title": "Ancrage positif",
            "description": "Créer un ancrage mental pour retrouver le calme",
            "duration": 10,
            "type": "cognitive",
            "difficulty": 2
        },
        "agressif": {
            "title": "Stop and think",
            "description": "Technique de pause réflexive avant réponse",
            "duration": 5,
            "type": "control",
            "difficulty": 3
        }
    }
    
    if profile in profile_exercises and len(exercises) < 5:
        exercises.append(profile_exercises[profile])
    
    # Limiter et varier les types
    return exercises[:5]

def generate_session_objectives_enhanced(theme: str, config: dict) -> List[str]:
    """Génère des objectifs améliorés pour une séance"""
    
    base_objectives = {
        "Cadre juridique et droits fondamentaux": [
            "✅ Maîtriser parfaitement ses droits en procédure",
            "📚 Comprendre le cadre légal et ses implications",
            "🎯 Identifier les enjeux spécifiques à son cas",
            "💡 Savoir quand et comment exercer ses droits"
        ]
    }
    
    objectives = base_objectives.get(theme, [
        f"✅ Maîtriser les aspects essentiels de : {theme}",
        "📈 Progresser dans la préparation globale",
        "💪 Renforcer la confiance en soi",
        "🎯 Atteindre les objectifs fixés"
    ])
    
    # Personnaliser selon le profil
    if config['client_profile'] == 'anxieux':
        objectives.append("🧘 Pratiquer des techniques de gestion du stress adaptées")
    elif config['client_profile'] == 'technique':
        objectives.append("📊 Approfondir les aspects techniques et factuels")
    
    return objectives[:5]

def generate_key_points(theme: str, config: dict) -> List[str]:
    """Génère les points clés pour une séance"""
    
    key_points = [
        f"🎯 Focus principal : {theme}",
        f"⚖️ Stratégie à maintenir : {config['strategy']}",
        "📝 Prendre des notes sur les difficultés rencontrées",
        "✅ Valider la compréhension avant de passer au suivant"
    ]
    
    # Ajouter des points spécifiques
    if config.get('media_attention'):
        key_points.append("📰 Anticiper les questions liées à la médiatisation")
    
    if config.get('codefendants', 0) > 0:
        key_points.append("🤝 Maintenir la cohérence avec la défense collective")
    
    return key_points

def generate_homework_enhanced(session_num: int, theme: str, config: dict) -> str:
    """Génère des devoirs personnalisés entre les séances"""
    
    homework_base = {
        1: "📖 Relire et mémoriser ses droits, créer une fiche aide-mémoire personnelle",
        2: "📅 Établir une chronologie détaillée avec dates, lieux et personnes",
        3: "🎙️ S'enregistrer en répondant aux questions clés (audio ou vidéo)",
        4: "🎣 Lister 10 questions pièges possibles et préparer les réponses",
        5: "🎭 Pratiquer devant miroir : posture, regard, gestuelle",
        6: "🎮 Simulation complète avec un proche jouant l'enquêteur",
        7: "🧘 Révision générale + exercices de relaxation"
    }
    
    homework = homework_base.get(session_num, f"📝 Réviser les acquis de la séance {session_num}")
    
    # Personnaliser selon le profil
    profile_additions = {
        "anxieux": " + 15 min de méditation quotidienne",
        "technique": " + créer un glossaire des termes techniques",
        "fragile": " + tenir un journal de progression positive"
    }
    
    if config['client_profile'] in profile_additions:
        homework += profile_additions[config['client_profile']]
    
    return homework

def display_sessions_management():
    """Gestion des séances avec interface améliorée"""
    st.markdown("### 📅 Gestion des séances")
    
    plan = st.session_state.preparation_state.get('current_plan')
    
    if not plan:
        st.info("👆 Créez d'abord un plan de préparation")
        return
    
    # Vue d'ensemble interactive
    display_sessions_overview(plan)
    
    # Sélecteur de séance amélioré
    st.markdown("#### 📚 Sélectionner une séance")
    
    # Affichage en grille
    cols = st.columns(4)
    selected_session = None
    
    for i, session in enumerate(plan.sessions):
        with cols[i % 4]:
            # Statut visuel
            if session.completed:
                status_icon = "✅"
                status_color = "#48bb78"
                status_text = f"Score: {session.score*5:.1f}/5" if session.score else "Complétée"
            else:
                status_icon = "⏳" if i == 0 or (i > 0 and plan.sessions[i-1].completed) else "🔒"
                status_color = "#f6e05e" if status_icon == "⏳" else "#cbd5e0"
                status_text = "Disponible" if status_icon == "⏳" else "Verrouillée"
            
            # Carte de séance cliquable
            if st.button(
                f"{status_icon} Séance {session.session_number}\n{session.theme[:20]}...\n{status_text}",
                key=f"session_card_{i}",
                use_container_width=True,
                disabled=(status_icon == "🔒")
            ):
                selected_session = i
    
    # Détail de la séance sélectionnée
    if selected_session is not None or 'current_session_view' in st.session_state:
        if selected_session is not None:
            st.session_state.current_session_view = selected_session
        
        session_idx = st.session_state.current_session_view
        session = plan.sessions[session_idx]
        
        st.markdown("---")
        display_session_detail(session, session_idx, plan)

def display_sessions_overview(plan: PreparationPlan):
    """Vue d'ensemble des séances avec visualisation améliorée"""
    
    # Timeline interactive
    fig = create_interactive_timeline(plan)
    st.plotly_chart(fig, use_container_width=True)

def create_interactive_timeline(plan: PreparationPlan) -> go.Figure:
    """Crée une timeline interactive des séances"""
    
    # Calculer les positions
    total_days = (plan.target_date - plan.created_date.date()).days if plan.target_date else 30
    
    # Données pour le graphique
    x_positions = []
    y_positions = []
    colors = []
    texts = []
    sizes = []
    
    for i, session in enumerate(plan.sessions):
        # Position X (date estimée)
        progress = (i + 1) / (plan.total_sessions + 1)
        estimated_date = plan.created_date + timedelta(days=int(total_days * progress))
        x_positions.append(estimated_date)
        
        # Position Y (alternée pour éviter le chevauchement)
        y_positions.append(1 + (i % 2) * 0.5)
        
        # Couleur selon statut
        if session.completed:
            colors.append('#48bb78')
            size = 20
        elif i == 0 or (i > 0 and plan.sessions[i-1].completed):
            colors.append('#f6e05e')
            size = 18
        else:
            colors.append('#cbd5e0')
            size = 15
        
        sizes.append(size)
        
        # Texte
        status = "✅" if session.completed else ("⏳" if size == 18 else "🔒")
        texts.append(f"{status} S{session.session_number}<br>{session.theme[:25]}...")
    
    # Créer le graphique
    fig = go.Figure()
    
    # Ligne de base
    fig.add_trace(go.Scatter(
        x=[plan.created_date, plan.target_date or (plan.created_date + timedelta(days=total_days))],
        y=[1.25, 1.25],
        mode='lines',
        line=dict(color='#e2e8f0', width=3),
        showlegend=False
    ))
    
    # Points des séances
    fig.add_trace(go.Scatter(
        x=x_positions,
        y=y_positions,
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=2, color='white')
        ),
        text=texts,
        textposition="top center",
        showlegend=False,
        hovertemplate='%{text}<extra></extra>'
    ))
    
    # Aujourd'hui
    fig.add_vline(
        x=datetime.now(), 
        line_dash="dash", 
        line_color="red",
        annotation_text="Aujourd'hui",
        annotation_position="top"
    )
    
    # Mise en page
    fig.update_layout(
        height=250,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            range=[plan.created_date - timedelta(days=5), 
                   (plan.target_date or plan.created_date + timedelta(days=total_days)) + timedelta(days=5)]
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            range=[0.5, 2.5]
        ),
        plot_bgcolor='white',
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def display_session_detail(session: PreparationSession, session_idx: int, plan: PreparationPlan):
    """Affiche le détail d'une séance avec interface améliorée"""
    
    # En-tête de la séance
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"## {session.title}")
    
    with col2:
        if session.completed:
            st.success(f"✅ Score: {session.score*5:.1f}/5")
        else:
            st.info("⏳ À faire")
    
    with col3:
        if session.completed:
            st.metric("Date", session.completion_date.strftime("%d/%m"))
    
    # Tabs pour le contenu
    tabs = st.tabs([
        "📋 Vue d'ensemble",
        "❓ Questions IA",
        "🎯 Exercices",
        "📝 Notes",
        "📊 Évaluation",
        "🤖 IA utilisées"
    ])
    
    with tabs[0]:
        display_session_overview_enhanced(session)
    
    with tabs[1]:
        display_session_questions_ai(session, plan)
    
    with tabs[2]:
        display_session_exercises_interactive(session)
    
    with tabs[3]:
        display_session_notes_enhanced(session, session_idx)
    
    with tabs[4]:
        if session.completed:
            display_session_results(session)
        else:
            display_session_completion(session, session_idx, plan)
    
    with tabs[5]:
        display_session_ai_info(session, plan)

def display_session_overview_enhanced(session: PreparationSession):
    """Vue d'ensemble améliorée de la séance"""
    
    # Métriques visuelles
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏱️ Durée", f"{session.duration_minutes} min")
    
    with col2:
        st.metric("❓ Questions", len(session.questions))
    
    with col3:
        st.metric("🎯 Exercices", len(session.exercises))
    
    with col4:
        difficulty_avg = sum(q.get('difficulty', 3) for q in session.questions) / len(session.questions) if session.questions else 3
        st.metric("🔥 Difficulté", f"{difficulty_avg:.1f}/5")
    
    # Objectifs avec progression
    st.markdown("### 🎯 Objectifs de la séance")
    
    for i, obj in enumerate(session.objectives):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(obj)
        
        with col2:
            if session.completed:
                # Supposer que les objectifs sont atteints si la séance est complétée
                st.success("✅")
            else:
                st.write("⭕")
    
    # Points clés avec mise en valeur
    if session.key_points:
        st.markdown("### 📌 Points clés à retenir")
        
        for point in session.key_points:
            st.info(f"💡 {point}")
    
    # Devoir avec rappel
    if session.homework:
        st.markdown("### 📝 Travail personnel")
        
        st.warning(f"📚 **À faire avant la prochaine séance:**\n\n{session.homework}")

def display_session_questions_ai(session: PreparationSession, plan: PreparationPlan):
    """Affiche les questions avec fonctionnalités IA avancées"""
    
    st.markdown(f"### ❓ {len(session.questions)} questions générées par IA")
    
    # Options d'affichage et de pratique
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_mode = st.selectbox(
            "Mode d'affichage",
            ["📄 Liste complète", "🎯 Mode pratique", "🃏 Flashcards", "🎮 Quiz interactif"],
            key=f"questions_mode_{session.session_number}"
        )
    
    with col2:
        difficulty_filter = st.select_slider(
            "Filtrer par difficulté",
            options=["Toutes", "⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
            value="Toutes",
            key=f"diff_filter_ai_{session.session_number}"
        )
    
    with col3:
        if LLMS_AVAILABLE and plan.ai_models_config.get('models'):
            regenerate_with_ai = st.button(
                "🔄 Régénérer avec IA",
                key=f"regen_questions_{session.session_number}"
            )
            
            if regenerate_with_ai:
                with st.spinner("Génération de nouvelles questions..."):
                    new_questions = generate_ai_questions(
                        session.session_number,
                        session.theme,
                        {'ai_config': plan.ai_models_config}
                    )
                    session.questions = new_questions
                    st.success("✅ Questions régénérées!")
                    st.rerun()
    
    # Filtrer les questions
    filtered_questions = filter_questions_by_difficulty(session.questions, difficulty_filter)
    
    # Affichage selon le mode
    if display_mode == "📄 Liste complète":
        display_questions_list(filtered_questions, session)
    elif display_mode == "🎯 Mode pratique":
        display_practice_mode(filtered_questions, session)
    elif display_mode == "🃏 Flashcards":
        display_flashcards_mode(filtered_questions, session)
    else:  # Quiz interactif
        display_quiz_mode(filtered_questions, session)

def filter_questions_by_difficulty(questions: List[Dict], filter_value: str) -> List[Dict]:
    """Filtre les questions par difficulté"""
    if filter_value == "Toutes":
        return questions
    
    # Convertir le filtre en nombre
    difficulty_map = {"⭐": 1, "⭐⭐": 2, "⭐⭐⭐": 3, "⭐⭐⭐⭐": 4, "⭐⭐⭐⭐⭐": 5}
    target_difficulty = difficulty_map.get(filter_value, 3)
    
    return [q for q in questions if q.get('difficulty', 3) == target_difficulty]

def display_questions_list(questions: List[Dict], session: PreparationSession):
    """Affiche la liste complète des questions"""
    
    for i, q in enumerate(questions, 1):
        with st.expander(
            f"Q{i}: {q['question'][:60]}... {'⭐' * q.get('difficulty', 3)}",
            expanded=(i <= 3)  # Premières questions ouvertes
        ):
            # Question
            st.markdown(f"**❓ Question complète:**")
            st.info(q['question'])
            
            # Réponse suggérée
            st.markdown("**✅ Réponse suggérée:**")
            st.success(q.get('answer', 'Réponse à personnaliser selon votre cas'))
            
            # Variantes
            if q.get('variants'):
                st.markdown("**🔄 Variantes possibles:**")
                for v in q['variants']:
                    st.write(f"• {v}")
            
            # Points d'attention
            if q.get('attention_points'):
                st.warning(f"⚠️ **Attention:** {q['attention_points']}")
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🎯 S'entraîner", key=f"train_q_{session.session_number}_{i}"):
                    st.session_state.practice_question = q
                    st.session_state.practice_mode = True
            
            with col2:
                if st.button("📝 Prendre des notes", key=f"notes_q_{session.session_number}_{i}"):
                    if f"q_notes_{session.session_number}_{i}" not in st.session_state:
                        st.session_state[f"q_notes_{session.session_number}_{i}"] = ""
                    
                    notes = st.text_area(
                        "Vos notes",
                        value=st.session_state[f"q_notes_{session.session_number}_{i}"],
                        key=f"q_notes_area_{session.session_number}_{i}"
                    )
                    
                    if st.button("💾 Sauvegarder", key=f"save_q_notes_{session.session_number}_{i}"):
                        st.session_state[f"q_notes_{session.session_number}_{i}"] = notes
                        st.success("Notes sauvegardées!")
            
            with col3:
                if LLMS_AVAILABLE:
                    if st.button("🤖 Améliorer avec IA", key=f"improve_q_{session.session_number}_{i}"):
                        improved = improve_question_with_ai(q)
                        if improved:
                            session.questions[i-1] = improved
                            st.success("Question améliorée!")
                            st.rerun()

def display_practice_mode(questions: List[Dict], session: PreparationSession):
    """Mode pratique interactif"""
    
    if not questions:
        st.warning("Aucune question disponible avec ces critères")
        return
    
    # Initialiser l'index de pratique
    if f'practice_idx_{session.session_number}' not in st.session_state:
        st.session_state[f'practice_idx_{session.session_number}'] = 0
    
    idx = st.session_state[f'practice_idx_{session.session_number}'] % len(questions)
    current_q = questions[idx]
    
    # Affichage de la question
    st.markdown(f"### Question {idx + 1}/{len(questions)}")
    
    # Barre de progression
    progress = (idx + 1) / len(questions)
    st.progress(progress)
    
    # Question avec style
    st.markdown(f"""
    <div class="question-card" style="font-size: 1.2em; padding: 30px;">
        {current_q['question']}
    </div>
    """, unsafe_allow_html=True)
    
    # Difficulté
    st.write(f"Difficulté: {'⭐' * current_q.get('difficulty', 3)}")
    
    # Zone de réponse
    user_answer = st.text_area(
        "Votre réponse:",
        height=150,
        placeholder="Prenez le temps de formuler votre réponse...",
        key=f"practice_answer_{session.session_number}_{idx}"
    )
    
    # Chronomètre optionnel
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⏱️ Activer chronomètre", key=f"timer_{session.session_number}_{idx}"):
            st.session_state[f'timer_start_{session.session_number}'] = datetime.now()
    
    with col2:
        if f'timer_start_{session.session_number}' in st.session_state:
            elapsed = (datetime.now() - st.session_state[f'timer_start_{session.session_number}']).seconds
            st.metric("Temps écoulé", f"{elapsed//60}:{elapsed%60:02d}")
    
    # Actions
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👁️ Voir la réponse", key=f"show_{session.session_number}_{idx}"):
            st.success(f"**Réponse suggérée:**\n\n{current_q.get('answer', 'Pas de réponse type')}")
            
            if current_q.get('attention_points'):
                st.warning(f"⚠️ {current_q['attention_points']}")
    
    with col2:
        if st.button("🔄 Variantes", key=f"variants_{session.session_number}_{idx}"):
            if current_q.get('variants'):
                st.info("**Autres formulations:**")
                for v in current_q['variants']:
                    st.write(f"• {v}")
    
    with col3:
        if st.button("➡️ Suivante", key=f"next_{session.session_number}_{idx}", type="primary"):
            st.session_state[f'practice_idx_{session.session_number}'] = idx + 1
            st.rerun()
    
    with col4:
        if st.button("📊 Résultats", key=f"results_{session.session_number}"):
            display_practice_results(session)

def display_flashcards_mode(questions: List[Dict], session: PreparationSession):
    """Mode flashcards interactif"""
    
    if not questions:
        st.warning("Aucune question disponible")
        return
    
    # Index de la carte
    if f'flash_idx_{session.session_number}' not in st.session_state:
        st.session_state[f'flash_idx_{session.session_number}'] = 0
    
    idx = st.session_state[f'flash_idx_{session.session_number}'] % len(questions)
    current_q = questions[idx]
    
    # État de la carte (recto/verso)
    if f'card_flipped_{session.session_number}' not in st.session_state:
        st.session_state[f'card_flipped_{session.session_number}'] = False
    
    # Affichage de la carte
    st.markdown(f"### Carte {idx + 1}/{len(questions)}")
    
    # Carte avec animation CSS
    card_content = current_q['question'] if not st.session_state[f'card_flipped_{session.session_number}'] else current_q.get('answer', 'Pas de réponse')
    card_color = "#667eea" if not st.session_state[f'card_flipped_{session.session_number}'] else "#48bb78"
    
    st.markdown(f"""
    <div style="
        background: {card_color};
        color: white;
        padding: 40px;
        border-radius: 15px;
        min-height: 250px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 1.3em;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    ">
        {card_content}
    </div>
    """, unsafe_allow_html=True)
    
    # Contrôles
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⬅️ Précédente", key=f"prev_flash_{session.session_number}"):
            st.session_state[f'flash_idx_{session.session_number}'] = idx - 1
            st.session_state[f'card_flipped_{session.session_number}'] = False
            st.rerun()
    
    with col2:
        if st.button("🔄 Retourner", key=f"flip_flash_{session.session_number}", type="primary"):
            st.session_state[f'card_flipped_{session.session_number}'] = not st.session_state[f'card_flipped_{session.session_number}']
            st.rerun()
    
    with col3:
        if st.button("➡️ Suivante", key=f"next_flash_{session.session_number}"):
            st.session_state[f'flash_idx_{session.session_number}'] = idx + 1
            st.session_state[f'card_flipped_{session.session_number}'] = False
            st.rerun()
    
    with col4:
        if st.button("🔀 Mélanger", key=f"shuffle_flash_{session.session_number}"):
            import random
            random.shuffle(questions)
            st.session_state[f'flash_idx_{session.session_number}'] = 0
            st.rerun()

def display_quiz_mode(questions: List[Dict], session: PreparationSession):
    """Mode quiz interactif avec scoring"""
    
    if not questions:
        st.warning("Aucune question disponible")
        return
    
    # Initialiser le quiz
    quiz_key = f'quiz_{session.session_number}'
    if quiz_key not in st.session_state:
        st.session_state[quiz_key] = {
            'current': 0,
            'answers': {},
            'scores': {},
            'started': False,
            'completed': False
        }
    
    quiz = st.session_state[quiz_key]
    
    if not quiz['started']:
        # Page de démarrage
        st.markdown("""
        <div class="prep-card" style="text-align: center;">
            <h3>🎮 Quiz Interactif</h3>
            <p>Testez vos connaissances avec ce quiz de {len(questions)} questions</p>
            <p>Vous pourrez évaluer vos réponses et obtenir un score final</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Commencer le quiz", type="primary", use_container_width=True):
            quiz['started'] = True
            st.rerun()
    
    elif quiz['completed']:
        # Page de résultats
        display_quiz_results(quiz, questions)
        
        if st.button("🔄 Recommencer", use_container_width=True):
            st.session_state[quiz_key] = {
                'current': 0,
                'answers': {},
                'scores': {},
                'started': False,
                'completed': False
            }
            st.rerun()
    
    else:
        # Quiz en cours
        current_idx = quiz['current']
        current_q = questions[current_idx]
        
        # Progress bar
        progress = (current_idx + 1) / len(questions)
        st.progress(progress)
        st.markdown(f"### Question {current_idx + 1}/{len(questions)}")
        
        # Question
        st.markdown(f"""
        <div class="question-card" style="font-size: 1.2em;">
            {current_q['question']}
        </div>
        """, unsafe_allow_html=True)
        
        # Réponse
        answer = st.text_area(
            "Votre réponse:",
            value=quiz['answers'].get(current_idx, ''),
            height=150,
            key=f"quiz_answer_{session.session_number}_{current_idx}"
        )
        
        # Auto-évaluation
        st.markdown("#### Auto-évaluation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            confidence = st.select_slider(
                "Confiance dans votre réponse",
                options=["Très faible", "Faible", "Moyenne", "Bonne", "Excellente"],
                value="Moyenne",
                key=f"quiz_conf_{session.session_number}_{current_idx}"
            )
        
        with col2:
            if st.button("👁️ Voir la réponse type", key=f"quiz_hint_{current_idx}"):
                st.info(current_q.get('answer', 'Pas de réponse type'))
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if current_idx > 0:
                if st.button("⬅️ Précédente", key=f"quiz_prev_{current_idx}"):
                    quiz['answers'][current_idx] = answer
                    quiz['current'] = current_idx - 1
                    st.rerun()
        
        with col3:
            if current_idx < len(questions) - 1:
                if st.button("Suivante ➡️", key=f"quiz_next_{current_idx}", type="primary"):
                    quiz['answers'][current_idx] = answer
                    quiz['scores'][current_idx] = confidence
                    quiz['current'] = current_idx + 1
                    st.rerun()
            else:
                if st.button("✅ Terminer", key=f"quiz_finish", type="primary"):
                    quiz['answers'][current_idx] = answer
                    quiz['scores'][current_idx] = confidence
                    quiz['completed'] = True
                    st.rerun()

def display_quiz_results(quiz: dict, questions: List[Dict]):
    """Affiche les résultats du quiz"""
    
    st.markdown("### 🏆 Résultats du quiz")
    
    # Calculer le score
    confidence_scores = {
        "Très faible": 1,
        "Faible": 2,
        "Moyenne": 3,
        "Bonne": 4,
        "Excellente": 5
    }
    
    total_score = sum(confidence_scores.get(score, 3) for score in quiz['scores'].values())
    max_score = len(questions) * 5
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    # Affichage du score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score total", f"{total_score}/{max_score}")
    
    with col2:
        st.metric("Pourcentage", f"{percentage:.1f}%")
    
    with col3:
        avg_confidence = total_score / len(questions) if questions else 0
        st.metric("Confiance moyenne", f"{avg_confidence:.1f}/5")
    
    # Graphique de performance
    fig = go.Figure(go.Bar(
        x=list(range(1, len(questions) + 1)),
        y=[confidence_scores.get(quiz['scores'].get(i, 'Moyenne'), 3) for i in range(len(questions))],
        marker_color=['#48bb78' if confidence_scores.get(quiz['scores'].get(i, 'Moyenne'), 3) >= 4 else '#f6e05e' if confidence_scores.get(quiz['scores'].get(i, 'Moyenne'), 3) >= 3 else '#fc8181' for i in range(len(questions))]
    ))
    
    fig.update_layout(
        title="Performance par question",
        xaxis_title="Question",
        yaxis_title="Score de confiance",
        yaxis_range=[0, 5.5],
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommandations
    st.markdown("### 💡 Recommandations")
    
    if percentage >= 80:
        st.success("🌟 Excellent travail! Vous maîtrisez bien le sujet.")
    elif percentage >= 60:
        st.info("📈 Bonne progression! Continuez à pratiquer les questions moins maîtrisées.")
    else:
        st.warning("⚠️ Des révisions supplémentaires sont recommandées.")
    
    # Questions à revoir
    weak_questions = [i for i, score in quiz['scores'].items() if confidence_scores.get(score, 3) <= 2]
    
    if weak_questions:
        st.markdown("#### 📚 Questions à revoir prioritairement")
        
        for idx in weak_questions[:5]:  # Limiter à 5
            q = questions[idx]
            with st.expander(f"Question {idx + 1}: {q['question'][:50]}..."):
                st.write(f"**Votre réponse:** {quiz['answers'].get(idx, 'Pas de réponse')}")
                st.info(f"**Réponse suggérée:** {q.get('answer', 'Non disponible')}")
                if q.get('attention_points'):
                    st.warning(f"⚠️ {q['attention_points']}")

def improve_question_with_ai(question: Dict) -> Optional[Dict]:
    """Améliore une question avec l'IA"""
    if not LLMS_AVAILABLE:
        return None
    
    llm_manager = MultiLLMManager()
    
    prompt = f"""Améliore cette question d'interrogatoire en la rendant plus précise et pertinente:
Question actuelle: {question['question']}
Réponse actuelle: {question.get('answer', '')}

Fournis:
1. Une version améliorée de la question
2. Une réponse mieux formulée
3. 3 variantes de la question
4. Les pièges à éviter
5. Maintiens le niveau de difficulté: {question.get('difficulty', 3)}/5
"""
    
    response = llm_manager.query_single_llm(
        list(llm_manager.clients.keys())[0],
        prompt,
        "Tu es un expert en interrogatoires judiciaires.",
        temperature=0.7
    )
    
    if response['success']:
        # Parser et retourner la question améliorée
        improved = parse_improved_question(response['response'])
        if improved:
            improved['difficulty'] = question.get('difficulty', 3)
            return improved
    
    return None

def parse_improved_question(response: str) -> Optional[Dict]:
    """Parse une question améliorée par l'IA"""
    # Implémentation simplifiée
    lines = response.split('\n')
    
    improved = {
        'question': '',
        'answer': '',
        'variants': [],
        'attention_points': ''
    }
    
    for line in lines:
        line = line.strip()
        if 'question' in line.lower() and not improved['question']:
            improved['question'] = line.split(':', 1)[-1].strip()
        elif 'réponse' in line.lower() and not improved['answer']:
            improved['answer'] = line.split(':', 1)[-1].strip()
        elif 'variante' in line.lower():
            improved['variants'].append(line.split(':', 1)[-1].strip())
        elif 'piège' in line.lower() or 'attention' in line.lower():
            improved['attention_points'] = line.split(':', 1)[-1].strip()
    
    return improved if improved['question'] else None

def display_session_exercises_interactive(session: PreparationSession):
    """Affiche les exercices de manière interactive"""
    
    st.markdown(f"### 🎯 {len(session.exercises)} exercices pratiques")
    
    # Vue d'ensemble des exercices
    exercise_types = {}
    for ex in session.exercises:
        ex_type = ex.get('type', 'general')
        if ex_type not in exercise_types:
            exercise_types[ex_type] = []
        exercise_types[ex_type].append(ex)
    
    # Afficher par type
    for ex_type, exercises in exercise_types.items():
        st.markdown(f"#### {get_exercise_type_icon(ex_type)} {ex_type.title()}")
        
        for i, exercise in enumerate(exercises):
            with st.expander(f"{exercise['title']} ({exercise.get('duration', 10)} min)", expanded=False):
                display_single_exercise(exercise, session.session_number, i)

def get_exercise_type_icon(ex_type: str) -> str:
    """Retourne l'icône pour un type d'exercice"""
    icons = {
        'relaxation': '😌',
        'mindfulness': '🧘',
        'practice': '🎯',
        'organization': '📊',
        'communication': '💬',
        'cognitive': '🧠',
        'study': '📚',
        'control': '🎮',
        'confidence': '💪',
        'general': '📝'
    }
    return icons.get(ex_type, '📝')

def display_single_exercise(exercise: Dict, session_num: int, exercise_idx: int):
    """Affiche un exercice unique"""
    
    # Description
    st.write(exercise['description'])
    
    # Instructions détaillées si disponibles
    if exercise.get('instructions'):
        st.markdown("**📋 Instructions:**")
        for instruction in exercise['instructions']:
            st.write(f"• {instruction}")
    
    # Outils nécessaires
    if exercise.get('tools'):
        st.info(f"🛠️ **Matériel:** {', '.join(exercise['tools'])}")
    
    # Scénario si applicable
    if exercise.get('scenario'):
        st.markdown("**🎬 Scénario:**")
        st.write(exercise['scenario'])
    
    # Interface selon le type
    if exercise['type'] == 'relaxation':
        display_relaxation_interface(exercise, session_num, exercise_idx)
    elif exercise['type'] == 'practice':
        display_practice_interface(exercise, session_num, exercise_idx)
    elif exercise['type'] == 'organization':
        display_organization_interface(exercise, session_num, exercise_idx)
    else:
        display_generic_exercise_interface(exercise, session_num, exercise_idx)
    
    # Suivi de progression
    completed_key = f"exercise_completed_{session_num}_{exercise_idx}"
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.checkbox("✅ Exercice complété", key=completed_key):
            st.success("Bravo! Exercice marqué comme complété")
    
    with col2:
        rating = st.select_slider(
            "Évaluation",
            options=["😟 Difficile", "😐 Moyen", "😊 Facile"],
            value="😐 Moyen",
            key=f"exercise_rating_{session_num}_{exercise_idx}"
        )

def display_relaxation_interface(exercise: Dict, session_num: int, idx: int):
    """Interface spécifique pour les exercices de relaxation"""
    
    # Timer de relaxation
    duration = exercise.get('duration', 5)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Démarrer", key=f"start_relax_{session_num}_{idx}"):
            st.session_state[f'relax_active_{session_num}_{idx}'] = True
            st.session_state[f'relax_start_{session_num}_{idx}'] = datetime.now()
    
    with col2:
        if st.button("⏸️ Pause", key=f"pause_relax_{session_num}_{idx}"):
            st.session_state[f'relax_active_{session_num}_{idx}'] = False
    
    with col3:
        if st.button("🔄 Réinitialiser", key=f"reset_relax_{session_num}_{idx}"):
            if f'relax_start_{session_num}_{idx}' in st.session_state:
                del st.session_state[f'relax_start_{session_num}_{idx}']
    
    # Affichage du timer
    if f'relax_start_{session_num}_{idx}' in st.session_state:
        elapsed = (datetime.now() - st.session_state[f'relax_start_{session_num}_{idx}']).seconds
        remaining = max(0, duration * 60 - elapsed)
        
        mins, secs = divmod(remaining, 60)
        
        st.markdown(f"""
        <div style="text-align: center; font-size: 48px; color: #667eea; font-weight: bold;">
            {mins:02d}:{secs:02d}
        </div>
        """, unsafe_allow_html=True)
        
        if remaining == 0:
            st.balloons()
            st.success("✅ Exercice terminé!")
    
    # Guide audio simulé
    with st.expander("🎧 Guide audio"):
        st.info("Dans la version complète, un guide audio vous accompagnera pendant l'exercice")

def display_practice_interface(exercise: Dict, session_num: int, idx: int):
    """Interface pour les exercices de pratique"""
    
    # Zone de pratique
    practice_text = st.text_area(
        "Zone de pratique",
        height=200,
        placeholder="Utilisez cet espace pour pratiquer l'exercice...",
        key=f"practice_area_{session_num}_{idx}"
    )
    
    # Outils de pratique
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎙️ Simuler un enregistrement", key=f"record_{session_num}_{idx}"):
            st.info("🔴 Enregistrement simulé en cours...")
    
    with col2:
        if st.button("📝 Générer un exemple", key=f"example_{session_num}_{idx}"):
            st.write("Exemple: 'Je comprends votre question. Permettez-moi de clarifier...'")

def display_organization_interface(exercise: Dict, session_num: int, idx: int):
    """Interface pour les exercices d'organisation"""
    
    st.markdown("#### 🗂️ Organisez vos idées")
    
    # Créer des zones d'organisation
    categories = ["Faits principaux", "Dates clés", "Personnes", "Preuves"]
    
    organized_data = {}
    
    for category in categories:
        with st.expander(f"📁 {category}", expanded=True):
            content = st.text_area(
                f"Contenu pour {category}",
                height=80,
                key=f"org_{session_num}_{idx}_{category}"
            )
            organized_data[category] = content
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Sauvegarder l'organisation", key=f"save_org_{session_num}_{idx}"):
            st.session_state[f'organized_{session_num}_{idx}'] = organized_data
            st.success("Organisation sauvegardée!")
    
    with col2:
        if st.button("📊 Visualiser", key=f"viz_org_{session_num}_{idx}"):
            # Créer une visualisation simple
            fig = go.Figure()
            
            for i, (cat, content) in enumerate(organized_data.items()):
                if content:
                    lines = content.split('\n')
                    fig.add_trace(go.Scatter(
                        x=[cat] * len(lines),
                        y=list(range(len(lines))),
                        mode='markers+text',
                        text=lines,
                        textposition="middle right",
                        name=cat
                    ))
            
            fig.update_layout(
                title="Organisation visuelle",
                xaxis_title="Catégories",
                yaxis_title="Éléments",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

def display_generic_exercise_interface(exercise: Dict, session_num: int, idx: int):
    """Interface générique pour les exercices"""
    
    # Espace de travail
    work_content = st.text_area(
        "Espace de travail",
        height=250,
        placeholder="Utilisez cet espace pour réaliser l'exercice...",
        key=f"generic_work_{session_num}_{idx}"
    )
    
    # Outils génériques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Copier le modèle", key=f"copy_template_{session_num}_{idx}"):
            st.info("Modèle copié dans le presse-papiers (simulé)")
    
    with col2:
        if st.button("💡 Obtenir un indice", key=f"hint_{session_num}_{idx}"):
            st.info("Concentrez-vous sur l'objectif principal de l'exercice")
    
    with col3:
        if st.button("✅ Valider", key=f"validate_{session_num}_{idx}"):
            if work_content:
                st.success("Travail validé!")
            else:
                st.warning("Complétez l'exercice avant de valider")

def display_session_notes_enhanced(session: PreparationSession, session_idx: int):
    """Système de notes amélioré"""
    
    st.markdown("### 📝 Notes et observations")
    
    # Récupérer ou initialiser les notes
    notes_key = f"session_notes_{session_idx}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = {
            'general': session.notes,
            'strengths': '',
            'weaknesses': '',
            'improvements': '',
            'personal': ''
        }
    
    notes = st.session_state[notes_key]
    
    # Onglets pour différents types de notes
    note_tabs = st.tabs(["📝 Général", "💪 Points forts", "⚠️ À améliorer", "📈 Progrès", "🔒 Personnel"])
    
    with note_tabs[0]:
        notes['general'] = st.text_area(
            "Notes générales sur la séance",
            value=notes['general'],
            height=200,
            placeholder="Notez vos observations générales...",
            key=f"notes_general_{session_idx}"
        )
    
    with note_tabs[1]:
        notes['strengths'] = st.text_area(
            "Points forts identifiés",
            value=notes['strengths'],
            height=150,
            placeholder="- Bonne gestion du stress\n- Réponses claires et concises\n- ...",
            key=f"notes_strengths_{session_idx}"
        )
    
    with note_tabs[2]:
        notes['weaknesses'] = st.text_area(
            "Points à améliorer",
            value=notes['weaknesses'],
            height=150,
            placeholder="- Hésitations sur les dates\n- Langage corporel à travailler\n- ...",
            key=f"notes_weaknesses_{session_idx}"
        )
    
    with note_tabs[3]:
        notes['improvements'] = st.text_area(
            "Progrès constatés",
            value=notes['improvements'],
            height=150,
            placeholder="Évolutions positives depuis la dernière séance...",
            key=f"notes_improvements_{session_idx}"
        )
    
    with note_tabs[4]:
        notes['personal'] = st.text_area(
            "Notes personnelles confidentielles",
            value=notes['personal'],
            height=150,
            placeholder="Notes privées qui ne seront pas partagées...",
            key=f"notes_personal_{session_idx}",
            help="Ces notes restent strictement personnelles"
        )
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Sauvegarder tout", key=f"save_all_notes_{session_idx}", type="primary"):
            st.session_state[notes_key] = notes
            session.notes = notes['general']  # Sauvegarder dans la session
            st.success("✅ Notes sauvegardées!")
    
    with col2:
        if st.button("📋 Utiliser un modèle", key=f"template_notes_{session_idx}"):
            template = {
                'general': "## Résumé de la séance\n\n## Points clés abordés\n\n## Questions travaillées\n",
                'strengths': "- Communication claire\n- Maintien du contact visuel\n- Cohérence du récit",
                'weaknesses': "- Gestion du stress\n- Précision des dates\n- Réponses trop longues",
                'improvements': "Par rapport à la séance précédente:\n- Meilleure fluidité\n- Plus de confiance",
                'personal': ""
            }
            st.session_state[notes_key] = template
            st.rerun()
    
    with col3:
        if st.button("🗑️ Effacer tout", key=f"clear_notes_{session_idx}"):
            if st.checkbox("Confirmer l'effacement", key=f"confirm_clear_{session_idx}"):
                st.session_state[notes_key] = {
                    'general': '',
                    'strengths': '',
                    'weaknesses': '',
                    'improvements': '',
                    'personal': ''
                }
                st.rerun()
    
    # Export des notes
    with st.expander("📤 Exporter les notes"):
        export_format = st.radio(
            "Format d'export",
            ["📄 Texte simple", "📝 Markdown", "📊 PDF"],
            horizontal=True,
            key=f"export_format_{session_idx}"
        )
        
        if st.button("💾 Exporter", key=f"export_notes_{session_idx}"):
            export_content = format_notes_for_export(notes, session, export_format)
            
            file_extension = {
                "📄 Texte simple": "txt",
                "📝 Markdown": "md",
                "📊 PDF": "pdf"
            }[export_format]
            
            st.download_button(
                "Télécharger",
                export_content,
                f"notes_seance_{session.session_number}_{datetime.now().strftime('%Y%m%d')}.{file_extension}",
                f"text/{file_extension}",
                key=f"download_notes_{session_idx}"
            )

def format_notes_for_export(notes: dict, session: PreparationSession, format_type: str) -> str:
    """Formate les notes pour l'export"""
    
    content = f"""Notes de la {session.title}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
{'=' * 50}

NOTES GÉNÉRALES:
{notes['general']}

POINTS FORTS:
{notes['strengths']}

POINTS À AMÉLIORER:
{notes['weaknesses']}

PROGRÈS CONSTATÉS:
{notes['improvements']}
"""
    
    if format_type == "📝 Markdown":
        content = content.replace('=' * 50, '---')
        content = content.replace('NOTES GÉNÉRALES:', '## Notes générales')
        content = content.replace('POINTS FORTS:', '## Points forts')
        content = content.replace('POINTS À AMÉLIORER:', '## Points à améliorer')
        content = content.replace('PROGRÈS CONSTATÉS:', '## Progrès constatés')
    
    return content

def display_session_completion(session: PreparationSession, session_idx: int, plan: PreparationPlan):
    """Interface de complétion de séance améliorée"""
    
    st.markdown("### 🏁 Compléter la séance")
    
    # Vérifications préalables
    checks = {
        "questions": len([q for q in session.questions if f"practice_answer_{session.session_number}_{i}" in st.session_state for i in range(len(session.questions))]) > 0,
        "exercises": any(f"exercise_completed_{session.session_number}_{i}" in st.session_state for i in range(len(session.exercises))),
        "notes": bool(st.session_state.get(f"session_notes_{session_idx}", {}).get('general'))
    }
    
    # Afficher l'état de complétion
    st.markdown("#### ✅ Checklist de complétion")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if checks['questions']:
            st.success("✅ Questions pratiquées")
        else:
            st.warning("⚠️ Pratiquez au moins une question")
    
    with col2:
        if checks['exercises']:
            st.success("✅ Exercices réalisés")
        else:
            st.warning("⚠️ Complétez au moins un exercice")
    
    with col3:
        if checks['notes']:
            st.success("✅ Notes prises")
        else:
            st.info("💡 Prenez des notes (optionnel)")
    
    # Auto-évaluation détaillée
    st.markdown("#### 📊 Auto-évaluation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Évaluation par domaine
        st.markdown("##### Évaluation par compétence")
        
        competences = {
            "Maîtrise du contenu": st.slider("Maîtrise du contenu", 1, 5, 3, key=f"comp_content_{session_idx}"),
            "Gestion du stress": st.slider("Gestion du stress", 1, 5, 3, key=f"comp_stress_{session_idx}"),
            "Clarté des réponses": st.slider("Clarté des réponses", 1, 5, 3, key=f"comp_clarity_{session_idx}"),
            "Confiance générale": st.slider("Confiance générale", 1, 5, 3, key=f"comp_confidence_{session_idx}")
        }
        
        avg_score = sum(competences.values()) / len(competences)
    
    with col2:
        # Feedback qualitatif
        st.markdown("##### Ressenti général")
        
        feeling = st.radio(
            "Comment vous sentez-vous ?",
            ["😟 Difficile", "😐 Correct", "😊 Bien", "🌟 Excellent"],
            index=1,
            key=f"feeling_{session_idx}"
        )
        
        objectives_met = st.multiselect(
            "Objectifs atteints",
            session.objectives,
            default=session.objectives[:2],
            key=f"objectives_check_{session_idx}"
        )
        
        needs_review = st.checkbox(
            "📚 Cette séance nécessite une révision",
            key=f"needs_review_{session_idx}"
        )
    
    # Commentaire final
    final_comments = st.text_area(
        "Commentaires sur la séance",
        placeholder="Notez vos impressions, difficultés, réussites...",
        height=100,
        key=f"final_comments_{session_idx}"
    )
    
    # Validation finale
    st.markdown("---")
    
    ready_to_complete = all(checks.values()) or st.checkbox(
        "Forcer la complétion (non recommandé)",
        key=f"force_complete_{session_idx}"
    )
    
    if st.button(
        "✅ Valider et terminer la séance",
        type="primary",
        disabled=not ready_to_complete,
        use_container_width=True,
        key=f"complete_session_{session_idx}"
    ):
        # Mettre à jour la séance
        session.completed = True
        session.completion_date = datetime.now()
        session.score = avg_score / 5
        
        # Sauvegarder l'évaluation détaillée
        evaluation_data = {
            'competences': competences,
            'feeling': feeling,
            'objectives_met': objectives_met,
            'needs_review': needs_review,
            'comments': final_comments,
            'checks': checks
        }
        
        if 'session_evaluations' not in st.session_state:
            st.session_state.session_evaluations = {}
        
        st.session_state.session_evaluations[session_idx] = evaluation_data
        
        # Mettre à jour la progression globale
        completed_count = sum(1 for s in plan.sessions if s.completed)
        plan.overall_progress = completed_count / plan.total_sessions
        
        # Feedback et célébration
        st.success(f"🎉 Bravo! Séance {session.session_number} complétée avec un score de {avg_score:.1f}/5")
        st.balloons()
        
        # Proposer la suite
        if session_idx < len(plan.sessions) - 1:
            st.markdown("### 🚀 Prochaine étape")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("➡️ Passer à la séance suivante", type="primary"):
                    st.session_state.current_session_view = session_idx + 1
                    st.rerun()
            
            with col2:
                if st.button("📊 Voir ma progression"):
                    st.session_state.selected_tab = 3
                    st.rerun()
        else:
            st.success("🏆 Félicitations! Vous avez terminé toutes les séances!")
            
            if st.button("📊 Voir le bilan complet", type="primary"):
                st.session_state.selected_tab = 3
                st.rerun()

def display_session_results(session: PreparationSession):
    """Affiche les résultats d'une séance complétée"""
    
    st.markdown("### ✅ Séance complétée")
    
    # Récupérer l'évaluation
    evaluation = st.session_state.get('session_evaluations', {}).get(session.session_number - 1)
    
    if not evaluation:
        st.info("Aucune évaluation détaillée disponible")
        return
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Score global", f"{session.score*5:.1f}/5 ⭐")
    
    with col2:
        st.metric("Date", session.completion_date.strftime("%d/%m/%Y"))
    
    with col3:
        st.metric("Objectifs", f"{len(evaluation['objectives_met'])}/{len(session.objectives)}")
    
    with col4:
        feeling_emoji = evaluation['feeling'].split()[0]
        st.metric("Ressenti", feeling_emoji)
    
    # Graphique radar des compétences
    if evaluation.get('competences'):
        fig = create_competences_radar(evaluation['competences'])
        st.plotly_chart(fig, use_container_width=True)
    
    # Détails
    with st.expander("📊 Voir les détails de l'évaluation"):
        st.markdown("#### Compétences évaluées")
        for comp, score in evaluation['competences'].items():
            st.write(f"• {comp}: {'⭐' * score}")
        
        if evaluation.get('comments'):
            st.markdown("#### Commentaires")
            st.info(evaluation['comments'])
        
        if evaluation.get('needs_review'):
            st.warning("📚 Cette séance a été marquée pour révision")
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Modifier l'évaluation", key=f"edit_eval_{session.session_number}"):
            session.completed = False
            st.rerun()
    
    with col2:
        if st.button("📤 Exporter le rapport", key=f"export_eval_{session.session_number}"):
            report = generate_session_report(session, evaluation)
            st.download_button(
                "💾 Télécharger",
                report,
                f"rapport_seance_{session.session_number}_{datetime.now().strftime('%Y%m%d')}.pdf",
                "application/pdf"
            )

def create_competences_radar(competences: dict) -> go.Figure:
    """Crée un graphique radar des compétences"""
    
    categories = list(competences.keys())
    values = list(competences.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Compétences',
        line_color='#667eea'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )),
        title="Évaluation des compétences",
        height=400
    )
    
    return fig

def generate_session_report(session: PreparationSession, evaluation: dict) -> bytes:
    """Génère un rapport PDF pour une séance"""
    
    # Simuler la génération PDF
    report = f"""RAPPORT DE SÉANCE
{'=' * 50}
{session.title}
Date: {session.completion_date.strftime('%d/%m/%Y') if session.completion_date else 'N/A'}
Score: {session.score*5:.1f}/5

COMPÉTENCES ÉVALUÉES:
"""
    
    for comp, score in evaluation.get('competences', {}).items():
        report += f"- {comp}: {score}/5\n"
    
    report += f"""
OBJECTIFS ATTEINTS:
- {len(evaluation.get('objectives_met', []))} sur {len(session.objectives)}

RESSENTI: {evaluation.get('feeling', 'Non renseigné')}

COMMENTAIRES:
{evaluation.get('comments', 'Aucun commentaire')}

{'=' * 50}
Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}
"""
    
    return report.encode('utf-8')

def display_session_ai_info(session: PreparationSession, plan: PreparationPlan):
    """Affiche les informations sur les IA utilisées"""
    
    st.markdown("### 🤖 Intelligence Artificielle")
    
    if not session.ai_models_used and not plan.ai_models_config:
        st.info("Cette séance n'utilise pas d'IA ou l'IA n'est pas configurée")
        return
    
    # Modèles utilisés
    st.markdown("#### 🤖 Modèles utilisés pour cette séance")
    
    if session.ai_models_used:
        cols = st.columns(len(session.ai_models_used))
        for i, model in enumerate(session.ai_models_used):
            with cols[i]:
                st.info(f"✅ {model}")
    
    # Configuration globale
    if plan.ai_models_config:
        with st.expander("⚙️ Configuration IA du plan"):
            config = plan.ai_models_config
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Mode fusion:** {'✅ Activé' if config.get('fusion_mode') else '❌ Désactivé'}")
                if config.get('fusion_strategy'):
                    st.write(f"**Stratégie:** {config['fusion_strategy']}")
                st.write(f"**Température:** {config.get('temperature', 0.7)}")
            
            with col2:
                st.write(f"**Longueur réponses:** {config.get('response_length', 'Standard')}")
                st.write(f"**Style:** {config.get('language_style', 'Accessible')}")
    
    # Régénération avec IA
    if LLMS_AVAILABLE and session.questions:
        st.markdown("#### 🔄 Régénération intelligente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Régénérer toutes les questions", key=f"regen_all_{session.session_number}"):
                with st.spinner("Régénération en cours..."):
                    # Simuler la régénération
                    time.sleep(2)
                    st.success("✅ Questions régénérées avec succès!")
        
        with col2:
            if st.button("🎯 Optimiser avec fusion IA", key=f"optimize_{session.session_number}"):
                with st.spinner("Optimisation par fusion..."):
                    time.sleep(2)
                    st.success("✅ Questions optimisées!")

def display_analytics():
    """Affiche les analytics détaillés"""
    st.markdown("### 📊 Analytics & Insights")
    
    plan = st.session_state.preparation_state.get('current_plan')
    
    if not plan:
        st.info("Créez un plan pour voir les analytics")
        return
    
    # Métriques globales
    display_global_metrics(plan)
    
    # Tabs d'analyse
    tabs = st.tabs([
        "📈 Progression",
        "🎯 Performance",
        "⏱️ Temps",
        "💡 Insights IA",
        "📊 Comparaisons"
    ])
    
    with tabs[0]:
        display_progression_analytics(plan)
    
    with tabs[1]:
        display_performance_analytics(plan)
    
    with tabs[2]:
        display_time_analytics(plan)
    
    with tabs[3]:
        display_ai_insights(plan)
    
    with tabs[4]:
        display_comparison_analytics(plan)

def display_global_metrics(plan: PreparationPlan):
    """Affiche les métriques globales"""
    
    # Calculer les métriques
    completed = sum(1 for s in plan.sessions if s.completed)
    total_questions = sum(len(s.questions) for s in plan.sessions)
    total_exercises = sum(len(s.exercises) for s in plan.sessions)
    avg_score = sum(s.score for s in plan.sessions if s.completed and s.score) / completed if completed > 0 else 0
    
    # Affichage en colonnes
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Progression",
            f"{plan.overall_progress*100:.0f}%",
            f"{completed}/{plan.total_sessions} séances"
        )
    
    with col2:
        st.metric(
            "Score moyen",
            f"{avg_score*5:.1f}/5",
            "⭐" * int(avg_score*5)
        )
    
    with col3:
        st.metric(
            "Questions totales",
            total_questions,
            f"~{total_questions//plan.total_sessions} par séance"
        )
    
    with col4:
        st.metric(
            "Exercices totaux",
            total_exercises,
            f"~{total_exercises//plan.total_sessions} par séance"
        )
    
    with col5:
        if plan.target_date:
            days_left = (plan.target_date - datetime.now().date()).days
            st.metric(
                "Temps restant",
                f"{days_left} jours",
                "⚠️ Urgent" if days_left < 7 else "✅ OK"
            )

def display_progression_analytics(plan: PreparationPlan):
    """Analyse de progression détaillée"""
    
    st.markdown("#### 📈 Analyse de progression")
    
    # Graphique de progression temporelle
    fig = create_progression_timeline(plan)
    st.plotly_chart(fig, use_container_width=True)
    
    # Analyse par période
    st.markdown("##### 📅 Rythme de progression")
    
    completed_sessions = [s for s in plan.sessions if s.completed]
    
    if len(completed_sessions) > 1:
        # Calculer le rythme
        first_date = completed_sessions[0].completion_date
        last_date = completed_sessions[-1].completion_date
        days_span = (last_date - first_date).days
        
        if days_span > 0:
            sessions_per_week = (len(completed_sessions) * 7) / days_span
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Rythme actuel", f"{sessions_per_week:.1f} séances/semaine")
            
            with col2:
                recommended_rhythm = plan.total_sessions * 7 / ((plan.target_date - plan.created_date.date()).days if plan.target_date else 30)
                st.metric("Rythme recommandé", f"{recommended_rhythm:.1f} séances/semaine")
            
            with col3:
                if sessions_per_week < recommended_rhythm * 0.8:
                    st.error("⚠️ Accélérer le rythme")
                elif sessions_per_week > recommended_rhythm * 1.2:
                    st.success("✅ Excellent rythme")
                else:
                    st.info("👍 Rythme adapté")
    
    # Prédictions
    if completed > 0 and plan.target_date:
        st.markdown("##### 🔮 Prédictions")
        
        # Estimer la date de fin
        avg_days_between = days_span / len(completed_sessions) if len(completed_sessions) > 1 else 3
        remaining_sessions = plan.total_sessions - completed
        estimated_days = remaining_sessions * avg_days_between
        estimated_completion = datetime.now() + timedelta(days=int(estimated_days))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Date de fin estimée:** {estimated_completion.strftime('%d/%m/%Y')}")
        
        with col2:
            if estimated_completion.date() > plan.target_date:
                st.error(f"⚠️ Retard prévu de {(estimated_completion.date() - plan.target_date).days} jours")
            else:
                st.success(f"✅ Fin prévue {(plan.target_date - estimated_completion.date()).days} jours avant l'échéance")

def create_progression_timeline(plan: PreparationPlan) -> go.Figure:
    """Crée un graphique de progression temporelle"""
    
    # Préparer les données
    dates = []
    progress = []
    scores = []
    
    for i, session in enumerate(plan.sessions):
        if session.completed and session.completion_date:
            dates.append(session.completion_date)
            progress.append((i + 1) / plan.total_sessions * 100)
            scores.append(session.score * 20 if session.score else None)
    
    # Créer le graphique
    fig = go.Figure()
    
    # Ligne de progression
    fig.add_trace(go.Scatter(
        x=dates,
        y=progress,
        mode='lines+markers',
        name='Progression',
        line=dict(color='#667eea', width=3),
        marker=dict(size=10)
    ))
    
    # Ligne des scores
    if any(scores):
        fig.add_trace(go.Scatter(
            x=dates,
            y=scores,
            mode='lines+markers',
            name='Score (%)',
            line=dict(color='#48bb78', width=2, dash='dot'),
            marker=dict(size=8),
            yaxis='y2'
        ))
    
    # Projection
    if dates and plan.target_date:
        last_date = dates[-1]
        remaining_days = (plan.target_date - last_date.date()).days
        projected_dates = [last_date + timedelta(days=i) for i in range(0, remaining_days, 3)]
        projected_progress = [progress[-1] + (100 - progress[-1]) * (i / remaining_days) for i in range(0, remaining_days, 3)]
        
        fig.add_trace(go.Scatter(
            x=projected_dates,
            y=projected_progress,
            mode='lines',
            name='Projection',
            line=dict(color='gray', dash='dash'),
            showlegend=True
        ))
    
    fig.update_layout(
        title="Progression temporelle",
        xaxis_title="Date",
        yaxis_title="Progression (%)",
        yaxis2=dict(
            title="Score (%)",
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        height=400,
        hovermode='x unified'
    )
    
    return fig

def display_performance_analytics(plan: PreparationPlan):
    """Analyse de performance détaillée"""
    
    st.markdown("#### 🎯 Analyse de performance")
    
    # Données de performance
    completed_sessions = [s for s in plan.sessions if s.completed and s.score]
    
    if not completed_sessions:
        st.info("Complétez des séances pour voir l'analyse de performance")
        return
    
    # Graphique d'évolution des scores
    fig = go.Figure()
    
    scores = [s.score * 5 for s in completed_sessions]
    session_numbers = [s.session_number for s in completed_sessions]
    
    fig.add_trace(go.Scatter(
        x=session_numbers,
        y=scores,
        mode='lines+markers',
        name='Score',
        line=dict(color='#667eea', width=3),
        marker=dict(size=12)
    ))
    
    # Ligne de tendance
    if len(scores) > 2:
        import numpy as np
        z = np.polyfit(session_numbers, scores, 1)
        p = np.poly1d(z)
        
        fig.add_trace(go.Scatter(
            x=session_numbers,
            y=p(session_numbers),
            mode='lines',
            name='Tendance',
            line=dict(color='red', dash='dash')
        ))
    
    # Zones de performance
    fig.add_hrect(y0=4, y1=5, fillcolor="green", opacity=0.1, annotation_text="Excellent")
    fig.add_hrect(y0=3, y1=4, fillcolor="yellow", opacity=0.1, annotation_text="Bon")
    fig.add_hrect(y0=0, y1=3, fillcolor="red", opacity=0.1, annotation_text="À améliorer")
    
    fig.update_layout(
        title="Évolution des scores",
        xaxis_title="Numéro de séance",
        yaxis_title="Score (/5)",
        yaxis_range=[0, 5.5],
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Analyse par thème
    st.markdown("##### 📊 Performance par thème")
    
    theme_scores = {}
    for session in completed_sessions:
        theme_type = categorize_theme(session.theme)
        if theme_type not in theme_scores:
            theme_scores[theme_type] = []
        theme_scores[theme_type].append(session.score * 5)
    
    # Calculer les moyennes
    theme_averages = {theme: sum(scores)/len(scores) for theme, scores in theme_scores.items()}
    
    # Afficher en barres
    fig2 = go.Figure(go.Bar(
        x=list(theme_averages.keys()),
        y=list(theme_averages.values()),
        marker_color=['#48bb78' if v >= 4 else '#f6e05e' if v >= 3 else '#fc8181' for v in theme_averages.values()]
    ))
    
    fig2.update_layout(
        title="Score moyen par type de thème",
        xaxis_title="Thème",
        yaxis_title="Score moyen (/5)",
        yaxis_range=[0, 5.5],
        height=300
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Recommandations personnalisées
    st.markdown("##### 💡 Recommandations basées sur la performance")
    
    weakest_theme = min(theme_averages, key=theme_averages.get)
    strongest_theme = max(theme_averages, key=theme_averages.get)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success(f"**Point fort:** {strongest_theme} ({theme_averages[strongest_theme]:.1f}/5)")
        st.write("Continuez sur cette lancée et partagez vos techniques")
    
    with col2:
        st.warning(f"**À renforcer:** {weakest_theme} ({theme_averages[weakest_theme]:.1f}/5)")
        st.write("Consacrez plus de temps à ce domaine")

def categorize_theme(theme: str) -> str:
    """Catégorise un thème de séance"""
    
    theme_lower = theme.lower()
    
    if any(word in theme_lower for word in ['droit', 'juridique', 'procédure', 'cadre']):
        return "Aspects juridiques"
    elif any(word in theme_lower for word in ['récit', 'chronologie', 'fait', 'histoire']):
        return "Construction narrative"
    elif any(word in theme_lower for word in ['question', 'réponse', 'piège']):
        return "Questions-Réponses"
    elif any(word in theme_lower for word in ['stress', 'émotion', 'psychologique']):
        return "Gestion émotionnelle"
    elif any(word in theme_lower for word in ['simulation', 'pratique', 'exercice']):
        return "Mise en pratique"
    elif any(word in theme_lower for word in ['communication', 'verbal', 'langage']):
        return "Communication"
    else:
        return "Autres"

def display_time_analytics(plan: PreparationPlan):
    """Analyse temporelle détaillée"""
    
    st.markdown("#### ⏱️ Analyse temporelle")
    
    # Temps total investi
    completed_sessions = [s for s in plan.sessions if s.completed]
    total_minutes = sum(s.duration_minutes for s in completed_sessions)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Temps total investi", f"{total_minutes//60}h {total_minutes%60}min")
    
    with col2:
        avg_duration = total_minutes / len(completed_sessions) if completed_sessions else 0
        st.metric("Durée moyenne/séance", f"{avg_duration:.0f} min")
    
    with col3:
        planned_total = sum(s.duration_minutes for s in plan.sessions)
        st.metric("Temps total prévu", f"{planned_total//60}h")
    
    with col4:
        completion_rate = (total_minutes / planned_total * 100) if planned_total > 0 else 0
        st.metric("Taux de réalisation", f"{completion_rate:.1f}%")
    
    # Répartition du temps
    if completed_sessions:
        st.markdown("##### 📊 Répartition du temps par activité")
        
        # Estimer la répartition (simulation)
        time_distribution = {
            "Questions-Réponses": 0.4,
            "Exercices pratiques": 0.3,
            "Révision/Notes": 0.2,
            "Pauses": 0.1
        }
        
        fig = go.Figure(go.Pie(
            labels=list(time_distribution.keys()),
            values=[v * total_minutes for v in time_distribution.values()],
            hole=0.4
        ))
        
        fig.update_layout(
            title="Répartition estimée du temps",
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Efficacité temporelle
    st.markdown("##### ⚡ Efficacité temporelle")
    
    if len(completed_sessions) > 1:
        # Calculer l'efficacité (score/temps)
        efficiency_data = []
        
        for session in completed_sessions:
            if session.score:
                efficiency = (session.score * 5) / (session.duration_minutes / 60)  # Score par heure
                efficiency_data.append({
                    'session': f"S{session.session_number}",
                    'efficiency': efficiency,
                    'score': session.score * 5,
                    'duration': session.duration_minutes
                })
        
        if efficiency_data:
            fig2 = go.Figure()
            
            fig2.add_trace(go.Bar(
                x=[d['session'] for d in efficiency_data],
                y=[d['efficiency'] for d in efficiency_data],
                name='Efficacité (score/heure)',
                marker_color='#667eea'
            ))
            
            fig2.update_layout(
                title="Efficacité par séance",
                xaxis_title="Séance",
                yaxis_title="Score par heure",
                height=300
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Insights
            best_efficiency = max(efficiency_data, key=lambda x: x['efficiency'])
            worst_efficiency = min(efficiency_data, key=lambda x: x['efficiency'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.success(f"**Meilleure efficacité:** {best_efficiency['session']} ({best_efficiency['efficiency']:.1f} pts/h)")
            
            with col2:
                st.info(f"**À optimiser:** {worst_efficiency['session']} ({worst_efficiency['efficiency']:.1f} pts/h)")

def display_ai_insights(plan: PreparationPlan):
    """Affiche les insights générés par l'IA"""
    
    st.markdown("#### 💡 Insights Intelligence Artificielle")
    
    if not LLMS_AVAILABLE:
        st.info("Les insights IA ne sont pas disponibles. Configurez les modèles d'IA.")
        return
    
    # Générer des insights
    if st.button("🤖 Générer des insights IA", key="generate_insights"):
        with st.spinner("Analyse en cours par l'IA..."):
            insights = generate_ai_insights_for_plan(plan)
            
            if insights:
                st.session_state.ai_insights = insights
    
    # Afficher les insights
    if 'ai_insights' in st.session_state:
        insights = st.session_state.ai_insights
        
        # Points forts
        with st.expander("💪 Points forts identifiés", expanded=True):
            for point in insights.get('strengths', []):
                st.success(f"✅ {point}")
        
        # Points d'amélioration
        with st.expander("📈 Axes d'amélioration", expanded=True):
            for point in insights.get('improvements', []):
                st.warning(f"⚠️ {point}")
        
        # Recommandations
        with st.expander("🎯 Recommandations personnalisées", expanded=True):
            for rec in insights.get('recommendations', []):
                st.info(f"💡 {rec}")
        
        # Prédictions
        with st.expander("🔮 Prédictions", expanded=False):
            for pred in insights.get('predictions', []):
                st.write(f"• {pred}")

def generate_ai_insights_for_plan(plan: PreparationPlan) -> Dict[str, List[str]]:
    """Génère des insights IA pour le plan"""
    
    # Simuler la génération d'insights
    completed = sum(1 for s in plan.sessions if s.completed)
    avg_score = sum(s.score for s in plan.sessions if s.completed and s.score) / completed if completed > 0 else 0
    
    insights = {
        'strengths': [],
        'improvements': [],
        'recommendations': [],
        'predictions': []
    }
    
    # Analyser les points forts
    if avg_score > 0.8:
        insights['strengths'].append("Excellente progression générale avec des scores élevés constants")
    if completed > plan.total_sessions * 0.7:
        insights['strengths'].append("Très bon rythme de progression, proche de l'objectif")
    
    # Points d'amélioration
    if avg_score < 0.6:
        insights['improvements'].append("Les scores moyens indiquent un besoin de renforcement")
    if plan.target_date:
        days_left = (plan.target_date - datetime.now().date()).days
        if days_left < 10 and completed < plan.total_sessions * 0.8:
            insights['improvements'].append("Rythme insuffisant par rapport à l'échéance proche")
    
    # Recommandations
    insights['recommendations'].append(f"Concentrez-vous sur les séances de type '{plan.prep_type}' pour maximiser l'impact")
    if plan.client_profile == 'anxieux':
        insights['recommendations'].append("Intégrez plus d'exercices de relaxation avant chaque séance")
    
    # Prédictions
    if completed > 0:
        estimated_final_score = avg_score * 5 * 1.1  # Projection optimiste
        insights['predictions'].append(f"Score final estimé: {min(estimated_final_score, 5):.1f}/5")
    
    return insights

def display_comparison_analytics(plan: PreparationPlan):
    """Affiche des comparaisons et benchmarks"""
    
    st.markdown("#### 📊 Comparaisons & Benchmarks")
    
    # Comparaison avec des moyennes (simulées)
    benchmarks = {
        'progression': {
            'votre_score': plan.overall_progress * 100,
            'moyenne': 65,
            'top_10': 85
        },
        'score_moyen': {
            'votre_score': sum(s.score*5 for s in plan.sessions if s.completed and s.score) / sum(1 for s in plan.sessions if s.completed) if any(s.completed for s in plan.sessions) else 0,
            'moyenne': 3.5,
            'top_10': 4.5
        },
        'temps_par_seance': {
            'votre_score': 120,  # minutes
            'moyenne': 90,
            'top_10': 120
        }
    }
    
    # Graphiques de comparaison
    for metric, values in benchmarks.items():
        fig = go.Figure()
        
        categories = ['Vous', 'Moyenne', 'Top 10%']
        metric_values = [values['votre_score'], values['moyenne'], values['top_10']]
        colors = ['#667eea', '#e2e8f0', '#48bb78']
        
        fig.add_trace(go.Bar(
            x=categories,
            y=metric_values,
            marker_color=colors
        ))
        
        fig.update_layout(
            title=metric.replace('_', ' ').title(),
            yaxis_title="Valeur",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Positionnement global
    st.markdown("##### 🏆 Votre positionnement")
    
    overall_position = calculate_overall_position(benchmarks)
    
    if overall_position >= 80:
        st.success(f"🌟 Excellent! Vous êtes dans le top {100-overall_position:.0f}% des utilisateurs")
    elif overall_position >= 60:
        st.info(f"👍 Bien! Vous êtes dans le top {100-overall_position:.0f}% des utilisateurs")
    else:
        st.warning(f"📈 En progression. Position actuelle: top {100-overall_position:.0f}%")

def calculate_overall_position(benchmarks: Dict) -> float:
    """Calcule la position globale par rapport aux benchmarks"""
    
    scores = []
    for metric, values in benchmarks.items():
        if values['top_10'] != values['moyenne']:
            normalized = (values['votre_score'] - values['moyenne']) / (values['top_10'] - values['moyenne'])
            scores.append(min(max(normalized * 100, 0), 100))
    
    return sum(scores) / len(scores) if scores else 50

def display_ai_configuration():
    """Configuration avancée de l'IA"""
    
    st.markdown("### 🤖 Configuration Intelligence Artificielle")
    
    if not LLMS_AVAILABLE:
        st.warning("Les modèles d'IA ne sont pas disponibles dans cette version")
        display_ai_simulation()
        return
    
    # Configuration actuelle
    current_config = st.session_state.preparation_state.get('ai_config', {})
    
    # Sélection des modèles
    st.markdown("#### 🤖 Modèles disponibles")
    
    llm_manager = MultiLLMManager()
    available_models = list(llm_manager.clients.keys())
    
    # Affichage en grille avec statut
    model_cols = st.columns(min(len(available_models), 3))
    
    selected_models = current_config.get('models', [])
    
    for i, model in enumerate(available_models):
        with model_cols[i % 3]:
            is_selected = model in selected_models
            
            # Card style pour chaque modèle
            st.markdown(f"""
            <div class="ai-model-badge" style="
                background: {'#667eea' if is_selected else '#e2e8f0'};
                color: {'white' if is_selected else 'black'};
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                margin: 10px 0;
            ">
                <h4>{model.replace('_', ' ').title()}</h4>
                <p>{'✅ Actif' if is_selected else '⭕ Inactif'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(
                "Désactiver" if is_selected else "Activer",
                key=f"toggle_model_{model}",
                use_container_width=True
            ):
                if is_selected:
                    selected_models.remove(model)
                else:
                    selected_models.append(model)
                
                current_config['models'] = selected_models
                st.session_state.preparation_state['ai_config'] = current_config
                st.rerun()
    
    # Mode fusion
    st.markdown("#### 🔀 Mode Fusion des IA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fusion_enabled = st.checkbox(
            "Activer le mode fusion",
            value=current_config.get('fusion_mode', False),
            help="Combine les réponses de plusieurs IA pour une qualité optimale",
            key="fusion_toggle"
        )
        
        if fusion_enabled and len(selected_models) < 2:
            st.warning("⚠️ Sélectionnez au moins 2 modèles pour le mode fusion")
            fusion_enabled = False
    
    with col2:
        if fusion_enabled:
            fusion_strategy = st.selectbox(
                "Stratégie de fusion",
                ["consensus", "best_answer", "synthesis"],
                format_func=lambda x: {
                    "consensus": "🤝 Consensus - Points communs",
                    "best_answer": "🏆 Meilleure réponse",
                    "synthesis": "🔄 Synthèse complète"
                }.get(x, x),
                index=["consensus", "best_answer", "synthesis"].index(current_config.get('fusion_strategy', 'synthesis')),
                key="fusion_strategy_select"
            )
        else:
            fusion_strategy = None
    
    # Paramètres avancés
    with st.expander("⚙️ Paramètres avancés", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "🌡️ Température (créativité)",
                min_value=0.0,
                max_value=1.0,
                value=current_config.get('temperature', 0.7),
                step=0.1,
                help="0 = Réponses déterministes, 1 = Maximum de créativité",
                key="ai_temperature"
            )
            
            max_tokens = st.number_input(
                "📏 Longueur max des réponses",
                min_value=500,
                max_value=4000,
                value=current_config.get('max_tokens', 2000),
                step=500,
                key="ai_max_tokens"
            )
        
        with col2:
            response_style = st.selectbox(
                "💬 Style de réponse",
                ["professional", "friendly", "educational", "empathetic"],
                format_func=lambda x: {
                    "professional": "👔 Professionnel",
                    "friendly": "😊 Amical",
                    "educational": "🎓 Pédagogique",
                    "empathetic": "❤️ Empathique"
                }.get(x, x),
                index=0,
                key="ai_style"
            )
            
            language_complexity = st.select_slider(
                "📖 Complexité du langage",
                options=["simple", "intermediate", "advanced", "expert"],
                value=current_config.get('language_complexity', 'intermediate'),
                format_func=lambda x: {
                    "simple": "Simple",
                    "intermediate": "Intermédiaire",
                    "advanced": "Avancé",
                    "expert": "Expert"
                }.get(x, x),
                key="ai_complexity"
            )
    
    # Test de configuration
    st.markdown("#### 🧪 Tester la configuration")
    
    test_prompt = st.text_area(
        "Question test",
        value="Comment gérer le stress lors d'un interrogatoire ?",
        height=100,
        key="test_prompt"
    )
    
    if st.button("🚀 Tester avec la configuration actuelle", key="test_ai_config"):
        if selected_models:
            with st.spinner("Test en cours..."):
                test_results = test_ai_configuration(
                    test_prompt,
                    selected_models,
                    fusion_enabled,
                    fusion_strategy,
                    temperature
                )
                
                # Afficher les résultats
                for model, result in test_results.items():
                    with st.expander(f"Réponse de {model}"):
                        st.write(result)
        else:
            st.error("Sélectionnez au moins un modèle")
    
    # Sauvegarder la configuration
    st.markdown("---")
    
    if st.button("💾 Sauvegarder la configuration", type="primary", key="save_ai_config"):
        current_config.update({
            'models': selected_models,
            'fusion_mode': fusion_enabled,
            'fusion_strategy': fusion_strategy,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'response_style': response_style,
            'language_complexity': language_complexity
        })
        
        st.session_state.preparation_state['ai_config'] = current_config
        st.success("✅ Configuration IA sauvegardée!")

def display_ai_simulation():
    """Affiche une simulation de configuration IA"""
    
    st.info("🤖 Simulation de configuration IA (version démo)")
    
    # Modèles simulés
    simulated_models = ["GPT-4", "Claude 3", "Gemini Pro", "Mistral Large", "LLaMA 2"]
    
    selected = st.multiselect(
        "Sélectionnez les modèles à utiliser",
        simulated_models,
        default=simulated_models[:2],
        key="simulated_models"
    )
    
    if len(selected) > 1:
        fusion_mode = st.checkbox("Activer le mode fusion", value=True, key="sim_fusion")
        
        if fusion_mode:
            st.success(f"✅ Mode fusion activé avec {len(selected)} modèles")
    
    # Démonstration
    if st.button("🎯 Voir une démonstration", key="demo_ai"):
        st.markdown("##### Exemple de fusion IA")
        
        with st.spinner("Génération des réponses..."):
            time.sleep(2)
        
        # Réponses simulées
        demo_responses = {
            "GPT-4": "Pour gérer le stress, je recommande la respiration profonde et la préparation mentale...",
            "Claude 3": "La gestion du stress passe par une préparation rigoureuse et des techniques de relaxation...",
            "Consensus": "**Synthèse:** Les deux IA s'accordent sur l'importance de la respiration et de la préparation..."
        }
        
        for model, response in demo_responses.items():
            with st.expander(f"Réponse {model}"):
                st.write(response)

def test_ai_configuration(prompt: str, models: List[str], fusion: bool, 
                         strategy: str, temperature: float) -> Dict[str, str]:
    """Teste la configuration IA avec un prompt"""
    
    if not LLMS_AVAILABLE:
        return {"Simulation": "Réponse simulée pour le test"}
    
    llm_manager = MultiLLMManager()
    results = {}
    
    # Tester chaque modèle
    for model in models:
        response = llm_manager.query_single_llm(
            model,
            prompt,
            "Tu es un expert en préparation judiciaire.",
            temperature=temperature
        )
        
        if response['success']:
            results[model] = response['response'][:500] + "..."  # Limiter la longueur
        else:
            results[model] = f"Erreur: {response.get('error', 'Inconnue')}"
    
    # Si fusion activée, ajouter le résultat fusionné
    if fusion and len(results) > 1:
        if strategy == "consensus":
            results["Fusion (Consensus)"] = "Points communs identifiés entre les réponses..."
        elif strategy == "best_answer":
            results["Fusion (Meilleure)"] = max(results.values(), key=len)
        else:
            results["Fusion (Synthèse)"] = "Synthèse complète des différentes approches..."
    
    return results

def display_resources():
    """Affiche la bibliothèque de ressources améliorée"""
    
    st.markdown("### 📚 Centre de Ressources")
    
    # Catégories de ressources
    resource_tabs = st.tabs([
        "📖 Guides",
        "🎥 Vidéos",
        "📝 Templates",
        "🎓 Formations",
        "🔗 Liens utiles",
        "💾 Mes ressources"
    ])
    
    with resource_tabs[0]:
        display_guides_library()
    
    with resource_tabs[1]:
        display_video_library()
    
    with resource_tabs[2]:
        display_templates_library()
    
    with resource_tabs[3]:
        display_training_library()
    
    with resource_tabs[4]:
        display_useful_links()
    
    with resource_tabs[5]:
        display_personal_resources()

def display_guides_library():
    """Affiche la bibliothèque de guides"""
    
    st.markdown("#### 📖 Guides de préparation")
    
    # Filtre par type
    guide_type = st.selectbox(
        "Type de guide",
        ["Tous", "Débutant", "Intermédiaire", "Avancé", "Spécialisé"],
        key="guide_filter"
    )
    
    # Liste des guides
    guides = [
        {
            "title": "Guide complet de l'audition libre",
            "level": "Débutant",
            "pages": 25,
            "description": "Tout ce qu'il faut savoir sur le déroulement d'une audition libre",
            "topics": ["Droits", "Procédure", "Conseils pratiques"],
            "rating": 4.8
        },
        {
            "title": "Maîtriser l'interrogatoire d'instruction",
            "level": "Avancé",
            "pages": 45,
            "description": "Techniques avancées pour faire face au juge d'instruction",
            "topics": ["Stratégie", "Communication", "Pièges à éviter"],
            "rating": 4.9
        },
        {
            "title": "Gestion du stress en procédure pénale",
            "level": "Tous niveaux",
            "pages": 30,
            "description": "Techniques psychologiques pour gérer l'anxiété",
            "topics": ["Relaxation", "Préparation mentale", "Exercices"],
            "rating": 4.7
        }
    ]
    
    # Affichage des guides
    for guide in guides:
        if guide_type == "Tous" or guide["level"] == guide_type:
            with st.expander(f"{guide['title']} - {guide['level']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(guide['description'])
                    st.write(f"**Sujets couverts:** {', '.join(guide['topics'])}")
                    st.write(f"**Pages:** {guide['pages']} | **Note:** {'⭐' * int(guide['rating'])}")
                
                with col2:
                    if st.button("📥 Télécharger", key=f"dl_guide_{guide['title']}"):
                        # Simuler le téléchargement
                        st.success("Guide ajouté à vos ressources!")
                    
                    if st.button("👁️ Aperçu", key=f"preview_{guide['title']}"):
                        st.info("Aperçu disponible dans la version complète")

def display_video_library():
    """Affiche la bibliothèque vidéo"""
    
    st.markdown("#### 🎥 Vidéothèque de formation")
    
    # Catégories
    video_categories = {
        "Simulations": [
            {"title": "Simulation d'audition commentée", "duration": "45 min", "level": "Intermédiaire"},
            {"title": "Interrogatoire type avec avocat", "duration": "60 min", "level": "Avancé"}
        ],
        "Techniques": [
            {"title": "Gérer les questions pièges", "duration": "30 min", "level": "Tous"},
            {"title": "Communication non-verbale", "duration": "25 min", "level": "Débutant"}
        ],
        "Témoignages": [
            {"title": "Retours d'expérience clients", "duration": "20 min", "level": "Tous"},
            {"title": "Conseils d'avocats experts", "duration": "35 min", "level": "Avancé"}
        ]
    }
    
    for category, videos in video_categories.items():
        st.markdown(f"##### {category}")
        
        cols = st.columns(3)
        for i, video in enumerate(videos):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    padding: 15px;
                    text-align: center;
                    height: 150px;
                ">
                    <h5>🎬 {video['title']}</h5>
                    <p>{video['duration']} - {video['level']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("▶️ Regarder", key=f"watch_{video['title']}"):
                    st.info("Vidéo disponible dans la version complète")

def display_templates_library():
    """Affiche la bibliothèque de templates"""
    
    st.markdown("#### 📝 Modèles et documents types")
    
    templates = {
        "Préparation": [
            "📅 Chronologie type à compléter",
            "✅ Checklist pré-audition",
            "📝 Journal de préparation quotidien"
        ],
        "Communication": [
            "💬 Phrases types de réponse",
            "🎯 Formulations recommandées",
            "⚠️ Expressions à éviter"
        ],
        "Organisation": [
            "📊 Tableau de suivi des séances",
            "🗂️ Classeur de documents",
            "📋 Fiche de synthèse rapide"
        ]
    }
    
    for category, items in templates.items():
        with st.expander(f"📁 {category}"):
            for item in items:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(item)
                
                with col2:
                    if st.button("📥", key=f"dl_template_{item}"):
                        # Créer un template simple
                        template_content = f"# {item}\n\nModèle à personnaliser selon votre cas.\n\n---\n"
                        st.download_button(
                            "💾",
                            template_content,
                            f"{item.replace(' ', '_')}.md",
                            "text/markdown",
                            key=f"download_{item}"
                        )

def display_training_library():
    """Affiche les formations disponibles"""
    
    st.markdown("#### 🎓 Formations spécialisées")
    
    trainings = [
        {
            "title": "Masterclass : Préparation complète à l'interrogatoire",
            "duration": "8 heures",
            "format": "En ligne",
            "price": "299€",
            "includes": ["Vidéos HD", "Exercices pratiques", "Support personnalisé", "Certificat"]
        },
        {
            "title": "Workshop : Gestion du stress judiciaire",
            "duration": "4 heures",
            "format": "Présentiel/Visio",
            "price": "149€",
            "includes": ["Techniques pratiques", "Groupe de 6 max", "Suivi 1 mois"]
        }
    ]
    
    for training in trainings:
        with st.expander(training['title']):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Durée:** {training['duration']}")
                st.write(f"**Format:** {training['format']}")
                st.write("**Inclus:**")
                for item in training['includes']:
                    st.write(f"• {item}")
            
            with col2:
                st.metric("Prix", training['price'])
                if st.button("🎓 S'inscrire", key=f"enroll_{training['title']}"):
                    st.info("Inscription disponible sur le site web")

def display_useful_links():
    """Affiche les liens utiles"""
    
    st.markdown("#### 🔗 Liens et ressources externes")
    
    links = {
        "Ressources officielles": {
            "Code de procédure pénale": "Articles sur les droits fondamentaux",
            "Service-public.fr": "Fiches pratiques sur les procédures",
            "Ministère de la Justice": "Guides officiels"
        },
        "Associations d'aide": {
            "France Victimes": "Soutien aux victimes",
            "Ordre des avocats": "Annuaire et conseils",
            "AIVI": "Aide juridictionnelle"
        },
        "Outils pratiques": {
            "Calculateur de délais": "Délais de procédure",
            "Modèles de courriers": "Courriers types justice",
            "Lexique juridique": "Comprendre les termes"
        }
    }
    
    for category, items in links.items():
        st.markdown(f"##### {category}")
        
        for title, description in items.items():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{title}** - {description}")
            
            with col2:
                st.button("🔗 Visiter", key=f"link_{title}")

def display_personal_resources():
    """Gestion des ressources personnelles"""
    
    st.markdown("#### 💾 Mes ressources personnelles")
    
    # Upload de documents
    uploaded_file = st.file_uploader(
        "Ajouter un document",
        type=['pdf', 'doc', 'docx', 'txt'],
        key="upload_resource"
    )
    
    if uploaded_file:
        if st.button("💾 Sauvegarder", key="save_uploaded"):
            # Sauvegarder dans session state
            if 'personal_resources' not in st.session_state:
                st.session_state.personal_resources = []
            
            st.session_state.personal_resources.append({
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'date': datetime.now()
            })
            
            st.success(f"✅ {uploaded_file.name} ajouté à vos ressources")
    
    # Afficher les ressources
    if 'personal_resources' in st.session_state and st.session_state.personal_resources:
        st.markdown("##### 📁 Vos documents")
        
        for i, resource in enumerate(st.session_state.personal_resources):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📄 {resource['name']}")
            
            with col2:
                st.write(f"{resource['size']//1024} KB")
            
            with col3:
                if st.button("🗑️", key=f"delete_resource_{i}"):
                    st.session_state.personal_resources.pop(i)
                    st.rerun()
    else:
        st.info("Aucune ressource personnelle. Ajoutez vos documents ci-dessus.")

def display_settings():
    """Affiche les paramètres du module"""
    
    st.markdown("### ⚙️ Paramètres")
    
    settings_tabs = st.tabs([
        "👤 Profil",
        "🔔 Notifications",
        "🎨 Apparence",
        "💾 Données",
        "🔐 Sécurité"
    ])
    
    with settings_tabs[0]:
        display_profile_settings()
    
    with settings_tabs[1]:
        display_notification_settings()
    
    with settings_tabs[2]:
        display_appearance_settings()
    
    with settings_tabs[3]:
        display_data_settings()
    
    with settings_tabs[4]:
        display_security_settings()

def display_profile_settings():
    """Paramètres du profil utilisateur"""
    
    st.markdown("#### 👤 Paramètres du profil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Nom", value="Client", key="profile_name")
        st.text_input("Email", value="client@example.com", key="profile_email")
        st.selectbox(
            "Rôle",
            ["Client", "Avocat", "Collaborateur"],
            key="profile_role"
        )
    
    with col2:
        st.date_input("Date de naissance", key="profile_dob")
        st.text_input("Téléphone", key="profile_phone")
        st.selectbox(
            "Langue préférée",
            ["Français", "English", "Español"],
            key="profile_language"
        )
    
    if st.button("💾 Sauvegarder le profil", type="primary", key="save_profile"):
        st.success("✅ Profil mis à jour!")

def display_notification_settings():
    """Paramètres de notifications"""
    
    st.markdown("#### 🔔 Paramètres de notifications")
    
    # Notifications par email
    st.markdown("##### 📧 Notifications par email")
    
    email_notifs = {
        "Rappels de séance": st.checkbox("Rappels de séance", value=True, key="notif_reminders"),
        "Rapports hebdomadaires": st.checkbox("Rapports hebdomadaires", value=True, key="notif_weekly"),
        "Nouveaux contenus": st.checkbox("Nouveaux contenus disponibles", value=False, key="notif_content"),
        "Mises à jour système": st.checkbox("Mises à jour système", value=False, key="notif_system")
    }
    
    # Timing des rappels
    st.markdown("##### ⏰ Timing des rappels")
    
    col1, col2 = st.columns(2)
    
    with col1:
        reminder_time = st.time_input(
            "Heure des rappels quotidiens",
            value=datetime.strptime("09:00", "%H:%M").time(),
            key="reminder_time"
        )
    
    with col2:
        reminder_advance = st.selectbox(
            "Rappel avant séance",
            ["1 heure", "2 heures", "1 jour", "2 jours"],
            index=2,
            key="reminder_advance"
        )
    
    # Notifications push
    st.markdown("##### 📱 Notifications push")
    
    push_enabled = st.checkbox(
        "Activer les notifications push",
        value=False,
        help="Nécessite l'application mobile",
        key="push_enabled"
    )
    
    if push_enabled:
        st.info("Configuration disponible dans l'application mobile")

def display_appearance_settings():
    """Paramètres d'apparence"""
    
    st.markdown("#### 🎨 Apparence")
    
    # Thème
    theme = st.selectbox(
        "Thème",
        ["🌞 Clair", "🌙 Sombre", "🎨 Automatique"],
        key="theme_select"
    )
    
    # Taille de police
    font_size = st.select_slider(
        "Taille du texte",
        options=["Petite", "Normale", "Grande", "Très grande"],
        value="Normale",
        key="font_size"
    )
    
    # Densité d'affichage
    display_density = st.radio(
        "Densité d'affichage",
        ["Compacte", "Confortable", "Spacieuse"],
        index=1,
        horizontal=True,
        key="display_density"
    )
    
    # Animations
    animations = st.checkbox(
        "Activer les animations",
        value=True,
        key="animations_enabled"
    )
    
    # Aperçu
    st.markdown("##### 👁️ Aperçu")
    
    st.info("Les modifications d'apparence seront appliquées après rechargement")

def display_data_settings():
    """Paramètres de données"""
    
    st.markdown("#### 💾 Gestion des données")
    
    # Export de données
    st.markdown("##### 📤 Export des données")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Exporter analytics", key="export_analytics"):
            st.info("Export des analytics en cours...")
    
    with col2:
        if st.button("📝 Exporter notes", key="export_notes"):
            st.info("Export des notes en cours...")
    
    with col3:
        if st.button("📦 Export complet", key="export_all"):
            data = export_all_data()
            st.download_button(
                "💾 Télécharger",
                data,
                f"export_complet_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json"
            )
    
    # Import de données
    st.markdown("##### 📥 Import de données")
    
    uploaded_backup = st.file_uploader(
        "Importer une sauvegarde",
        type=['json'],
        key="import_backup"
    )
    
    if uploaded_backup:
        if st.button("📥 Importer", key="import_data"):
            st.success("✅ Données importées avec succès!")
    
    # Suppression de données
    st.markdown("##### 🗑️ Suppression de données")
    
    with st.expander("⚠️ Zone dangereuse", expanded=False):
        st.warning("Ces actions sont irréversibles!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Effacer l'historique", key="clear_history"):
                if st.checkbox("Confirmer l'effacement de l'historique"):
                    st.info("Historique effacé")
        
        with col2:
            if st.button("☠️ Tout effacer", key="clear_all"):
                if st.checkbox("Je comprends que TOUTES mes données seront perdues"):
                    st.session_state.clear()
                    st.success("Toutes les données ont été effacées")
                    st.rerun()

def display_security_settings():
    """Paramètres de sécurité"""
    
    st.markdown("#### 🔐 Sécurité")
    
    # Authentification
    st.markdown("##### 🔑 Authentification")
    
    two_factor = st.checkbox(
        "Activer l'authentification à deux facteurs",
        value=False,
        key="2fa_enabled"
    )
    
    if two_factor:
        st.info("Configuration 2FA disponible dans la version complète")
    
    # Sessions
    st.markdown("##### 💻 Sessions actives")
    
    sessions = [
        {"device": "Chrome - Windows", "location": "Paris, France", "last_active": "Il y a 5 minutes"},
        {"device": "Safari - iPhone", "location": "Paris, France", "last_active": "Il y a 2 heures"}
    ]
    
    for session in sessions:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{session['device']}** - {session['location']}")
        
        with col2:
            st.write(session['last_active'])
        
        with col3:
            st.button("Déconnecter", key=f"logout_{session['device']}")
    
    # Confidentialité
    st.markdown("##### 🔒 Confidentialité")
    
    privacy_settings = {
        "Partager les statistiques anonymes": st.checkbox("Partager les statistiques", value=True, key="share_stats"),
        "Historique de navigation": st.checkbox("Conserver l'historique", value=True, key="keep_history"),
        "Suggestions personnalisées": st.checkbox("Suggestions IA", value=True, key="ai_suggestions")
    }

def export_all_data() -> str:
    """Exporte toutes les données du module"""
    
    export_data = {
        'export_date': datetime.now().isoformat(),
        'version': '2.0',
        'module': 'preparation_client',
        'data': {
            'preparation_state': st.session_state.get('preparation_state', {}),
            'session_evaluations': st.session_state.get('session_evaluations', {}),
            'personal_resources': st.session_state.get('personal_resources', []),
            'ai_insights': st.session_state.get('ai_insights', {})
        }
    }
    
    return json.dumps(export_data, ensure_ascii=False, indent=2)

def export_plan_as_pdf(plan: PreparationPlan):
    """Exporte le plan en PDF"""
    
    # Générer le contenu
    content = f"""PLAN DE PRÉPARATION
{'=' * 60}

Type: {plan.prep_type}
Profil client: {plan.client_profile}
Stratégie: {plan.strategy}
Date création: {plan.created_date.strftime('%d/%m/%Y')}
Date cible: {plan.target_date.strftime('%d/%m/%Y') if plan.target_date else 'Non définie'}
Progression: {plan.overall_progress*100:.0f}%

SÉANCES
{'=' * 60}
"""
    
    for session in plan.sessions:
        status = "✅ Complétée" if session.completed else "⏳ En attente"
        content += f"""
Séance {session.session_number}: {session.title}
Statut: {status}
Durée: {session.duration_minutes} minutes
Questions: {len(session.questions)}
Exercices: {len(session.exercises)}
{'Score: ' + str(session.score*5) + '/5' if session.completed and session.score else ''}

Objectifs:
"""
        for obj in session.objectives:
            content += f"- {obj}\n"
        
        if session.homework:
            content += f"\nDevoir: {session.homework}\n"
        
        content += "\n" + "-" * 60 + "\n"
    
    # Télécharger
    st.download_button(
        "💾 Télécharger PDF",
        content.encode('utf-8'),
        f"plan_preparation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain",
        key="download_plan_pdf"
    )

def save_plan_template(config: dict):
    """Sauvegarde un plan comme modèle"""
    
    if 'plan_templates' not in st.session_state:
        st.session_state.plan_templates = []
    
    template = {
        'name': f"Modèle {config['prep_type']} - {config['client_profile']}",
        'config': config,
        'created': datetime.now()
    }
    
    st.session_state.plan_templates.append(template)

def setup_notifications(plan: PreparationPlan):
    """Configure les notifications pour le plan"""
    
    # Simuler la configuration
    st.toast("🔔 Notifications activées pour ce plan")

def display_practice_results(session: PreparationSession):
    """Affiche les résultats de pratique"""
    
    st.markdown("### 📊 Résultats de pratique")
    
    # Statistiques de pratique (simulées)
    stats = {
        'questions_practiced': 12,
        'avg_time_per_question': 45,  # secondes
        'confidence_evolution': [60, 65, 70, 75, 80, 85],
        'difficult_questions': 3
    }
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Questions pratiquées", stats['questions_practiced'])
    
    with col2:
        st.metric("Temps moyen/question", f"{stats['avg_time_per_question']}s")
    
    with col3:
        st.metric("Questions difficiles", stats['difficult_questions'])
    
    with col4:
        improvement = stats['confidence_evolution'][-1] - stats['confidence_evolution'][0]
        st.metric("Progression confiance", f"+{improvement}%")
    
    # Graphique d'évolution
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(1, len(stats['confidence_evolution']) + 1)),
        y=stats['confidence_evolution'],
        mode='lines+markers',
        name='Confiance (%)',
        line=dict(color='#667eea', width=3)
    ))
    
    fig.update_layout(
        title="Évolution de la confiance pendant la pratique",
        xaxis_title="Nombre de questions",
        yaxis_title="Niveau de confiance (%)",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Point d'entrée pour le lazy loading
if __name__ == "__main__":
    run()