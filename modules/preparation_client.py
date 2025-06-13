# modules/preparation_client.py
"""Module de préparation des clients pour auditions et interrogatoires"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict
import json
from dataclasses import dataclass, asdict
import plotly.graph_objects as go
import plotly.express as px

from config.app_config import LLMProvider
from managers.multi_llm_manager import MultiLLMManager
from modules.dataclasses import PreparationClientResult
from utils.helpers import extract_section

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

def process_preparation_client_request(query: str, analysis: dict):
    """Traite une demande de préparation client"""
    
    st.markdown("### 👥 Préparation du client")
    
    # Nouveau système de navigation par onglets
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Nouvelle préparation",
        "📅 Plan de séances",
        "📊 Suivi progression",
        "📚 Bibliothèque",
        "⚙️ Paramètres"
    ])
    
    with tab1:
        # Configuration de la préparation
        config = display_enhanced_preparation_config(analysis)
        
        if st.button("🚀 Générer le plan de préparation", key="generate_prep_plan", type="primary"):
            with st.spinner("📋 Création du plan de préparation personnalisé..."):
                # Générer d'abord le contenu complet
                result = generate_client_preparation(config, analysis)
                
                if result:
                    # Créer le plan de séances
                    preparation_plan = create_preparation_sessions_plan(config, result, analysis)
                    
                    # Sauvegarder dans la session
                    st.session_state.preparation_client_result = result
                    st.session_state.preparation_plan = preparation_plan
                    
                    # Afficher le plan
                    display_preparation_plan_overview(preparation_plan)
    
    with tab2:
        if 'preparation_plan' in st.session_state:
            display_sessions_management(st.session_state.preparation_plan)
        else:
            st.info("👆 Créez d'abord un plan de préparation dans l'onglet 'Nouvelle préparation'")
    
    with tab3:
        if 'preparation_plan' in st.session_state:
            display_progress_tracking(st.session_state.preparation_plan)
        else:
            st.info("👆 Aucun plan de préparation en cours")
    
    with tab4:
        display_resources_library()
    
    with tab5:
        display_preparation_settings()

def display_enhanced_preparation_config(analysis: dict) -> dict:
    """Interface de configuration améliorée pour la préparation"""
    
    config = {}
    
    # En-tête avec informations contextuelles
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📅 Date du jour : {datetime.now().strftime('%d/%m/%Y')}")
    with col2:
        target_date = st.date_input(
            "📆 Date cible",
            value=datetime.now() + timedelta(days=30),
            key="target_date_input"
        )
        config['target_date'] = target_date
    
    # Configuration principale en colonnes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Type de préparation avec description
        config['prep_type'] = st.selectbox(
            "📋 Type de préparation",
            ["audition", "interrogatoire", "comparution", "confrontation", "expertise"],
            format_func=lambda x: {
                "audition": "👮 Audition (police/gendarmerie)",
                "interrogatoire": "👨‍⚖️ Interrogatoire (juge d'instruction)",
                "comparution": "⚖️ Comparution (tribunal)",
                "confrontation": "🤝 Confrontation",
                "expertise": "🔬 Expertise"
            }.get(x, x.title()),
            key="prep_type_select"
        )
        
        # Nombre de séances souhaité
        config['nb_sessions'] = st.slider(
            "📊 Nombre de séances",
            min_value=5,
            max_value=10,
            value=7,
            help="Nombre de séances de préparation à planifier",
            key="nb_sessions_slider"
        )
    
    with col2:
        # Profil du client avec évaluation
        config['profil_client'] = st.selectbox(
            "👤 Profil psychologique",
            ["anxieux", "confiant", "agressif", "fragile", "technique"],
            format_func=lambda x: {
                "anxieux": "😰 Anxieux - Besoin de réassurance",
                "confiant": "😊 Confiant - Maintenir la vigilance",
                "agressif": "😠 Agressif - Canaliser l'énergie",
                "fragile": "🥺 Fragile - Soutien renforcé",
                "technique": "🤓 Technique - Approche factuelle"
            }.get(x, x.title()),
            key="profil_select"
        )
        
        # Niveau d'expérience judiciaire
        config['experience_level'] = st.select_slider(
            "⚖️ Expérience judiciaire",
            options=["Novice", "Peu expérimenté", "Expérimenté", "Très expérimenté"],
            value="Peu expérimenté",
            key="experience_select"
        )
    
    with col3:
        # Stratégie de défense
        config['strategie'] = st.selectbox(
            "🎯 Stratégie",
            ["negation", "justification", "minimisation", "collaboration", "silence"],
            format_func=lambda x: {
                "negation": "❌ Négation totale",
                "justification": "✅ Justification des actes",
                "minimisation": "📉 Minimisation",
                "collaboration": "🤝 Collaboration mesurée",
                "silence": "🤐 Droit au silence"
            }.get(x, x.title()),
            key="strategie_select"
        )
        
        # Durée des séances
        config['session_duration'] = st.select_slider(
            "⏱️ Durée par séance",
            options=[60, 90, 120, 150, 180],
            value=120,
            format_func=lambda x: f"{x} minutes",
            key="session_duration_select"
        )
    
    # Section avancée
    with st.expander("🔧 Options avancées", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            config['focus_areas'] = st.multiselect(
                "🎯 Domaines prioritaires",
                [
                    "Gestion du stress",
                    "Cohérence du récit",
                    "Questions techniques",
                    "Langage corporel",
                    "Gestion des silences",
                    "Réponses aux pièges",
                    "Maintien de la stratégie"
                ],
                default=["Gestion du stress", "Cohérence du récit", "Réponses aux pièges"],
                key="focus_areas_select"
            )
            
            config['difficulty_progression'] = st.radio(
                "📈 Progression de difficulté",
                ["Progressive", "Constante", "Intensive"],
                index=0,
                key="difficulty_radio"
            )
        
        with col2:
            config['include_mock_sessions'] = st.checkbox(
                "🎮 Inclure séances de simulation",
                value=True,
                key="mock_sessions_check"
            )
            
            config['include_video_analysis'] = st.checkbox(
                "📹 Prévoir analyse vidéo",
                value=False,
                help="Pour travailler le langage non-verbal",
                key="video_analysis_check"
            )
            
            config['include_stress_tests'] = st.checkbox(
                "💪 Tests de résistance au stress",
                value=True,
                key="stress_tests_check"
            )
    
    # Contexte de l'affaire amélioré
    with st.expander("📂 Contexte détaillé de l'affaire", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            config['infractions'] = st.text_area(
                "⚖️ Infractions reprochées",
                value=analysis.get('infractions', ''),
                placeholder="Ex: Abus de biens sociaux, faux et usage de faux...",
                height=100,
                key="infractions_textarea"
            )
            
            config['complexity_level'] = st.select_slider(
                "🔥 Complexité de l'affaire",
                options=["Simple", "Modérée", "Complexe", "Très complexe"],
                value="Modérée",
                key="complexity_select"
            )
        
        with col2:
            config['elements_favorables'] = st.text_area(
                "✅ Éléments favorables",
                placeholder="- Absence de preuve directe\n- Témoignages favorables\n- Contexte atténuant",
                height=100,
                key="elements_favorables_textarea"
            )
            
            config['media_attention'] = st.checkbox(
                "📰 Affaire médiatisée",
                value=False,
                help="Nécessite une préparation spécifique",
                key="media_attention_check"
            )
    
    # Points sensibles avec catégorisation
    st.markdown("#### 🎯 Points sensibles à préparer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['factual_challenges'] = st.text_area(
            "📊 Difficultés factuelles",
            placeholder="- Incohérences dans les dates\n- Documents manquants\n- Témoignages contradictoires",
            height=80,
            key="factual_challenges_textarea"
        )
    
    with col2:
        config['emotional_challenges'] = st.text_area(
            "💭 Difficultés émotionnelles",
            placeholder="- Gestion de la culpabilité\n- Peur du jugement\n- Anxiété de performance",
            height=80,
            key="emotional_challenges_textarea"
        )
    
    return config

def create_preparation_sessions_plan(config: dict, result: PreparationClientResult, analysis: dict) -> PreparationPlan:
    """Crée un plan de séances détaillé"""
    
    nb_sessions = config.get('nb_sessions', 7)
    
    # Définir les thèmes selon le type de préparation
    themes_by_type = {
        "audition": [
            "Introduction et cadre juridique",
            "Travail sur le récit chronologique",
            "Gestion des questions factuelles",
            "Préparation aux questions pièges",
            "Langage corporel et attitude",
            "Simulation complète",
            "Révision et ajustements finaux"
        ],
        "interrogatoire": [
            "Droits et procédure d'instruction",
            "Construction du récit défensif",
            "Gestion des confrontations avec les preuves",
            "Questions techniques et expertise",
            "Stratégie face au magistrat",
            "Simulation d'interrogatoire",
            "Préparation psychologique finale"
        ],
        "comparution": [
            "Protocole et déroulement d'audience",
            "Présentation personnelle et parcours",
            "Exposition des faits",
            "Réponses aux questions du tribunal",
            "Gestion de la partie civile",
            "Plaidoirie personnelle",
            "Répétition générale"
        ],
        "confrontation": [
            "Cadre et enjeux de la confrontation",
            "Maintien de sa version",
            "Gestion des accusations",
            "Techniques de déstabilisation",
            "Communication non-violente",
            "Jeux de rôle",
            "Stratégies de sortie"
        ],
        "expertise": [
            "Nature et objectifs de l'expertise",
            "Préparation du discours",
            "Questions psychologiques types",
            "Cohérence avec le dossier",
            "Gestion des tests",
            "Simulation d'entretien",
            "Consolidation finale"
        ]
    }
    
    base_themes = themes_by_type.get(config['prep_type'], themes_by_type['audition'])
    
    # Adapter le nombre de thèmes au nombre de séances
    if nb_sessions > len(base_themes):
        # Ajouter des séances supplémentaires
        base_themes.extend([
            "Approfondissement des points sensibles",
            "Session de renforcement",
            "Préparation complémentaire"
        ])
    
    themes = base_themes[:nb_sessions]
    
    # Créer les séances
    sessions = []
    
    for i in range(nb_sessions):
        session_questions = generate_session_questions(
            i + 1, 
            themes[i], 
            config, 
            result,
            15 if i < nb_sessions - 2 else 20  # Plus de questions pour les dernières séances
        )
        
        session_exercises = generate_session_exercises(
            themes[i],
            config['profil_client'],
            config.get('focus_areas', [])
        )
        
        session = PreparationSession(
            session_number=i + 1,
            title=f"Séance {i + 1} : {themes[i]}",
            theme=themes[i],
            objectives=generate_session_objectives(themes[i], config),
            duration_minutes=config.get('session_duration', 120),
            questions=session_questions,
            exercises=session_exercises,
            key_points=extract_key_points_for_session(themes[i], result.content),
            homework=generate_homework(i + 1, themes[i], config)
        )
        
        sessions.append(session)
    
    # Créer le plan complet
    plan = PreparationPlan(
        total_sessions=nb_sessions,
        sessions=sessions,
        prep_type=config['prep_type'],
        client_profile=config['profil_client'],
        strategy=config['strategie'],
        created_date=datetime.now(),
        target_date=config.get('target_date')
    )
    
    return plan

def generate_session_questions(session_num: int, theme: str, config: dict, 
                              result: PreparationClientResult, num_questions: int = 15) -> List[Dict[str, str]]:
    """Génère des questions spécifiques pour une séance"""
    
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        return []
    
    prompt = f"""Génère {num_questions} questions spécifiques pour la séance {session_num} de préparation.

CONTEXTE:
- Type de procédure : {config['prep_type']}
- Thème de la séance : {theme}
- Profil client : {config['profil_client']}
- Stratégie : {config['strategie']}
- Infractions : {config.get('infractions', 'Non précisées')}

EXIGENCES:
1. Questions progressives en difficulté
2. Adaptées au thème de la séance
3. Incluant des variantes et reformulations
4. Avec des notes sur les pièges potentiels

Format pour chaque question:
- Question principale
- Réponse suggérée (courte et précise)
- Variantes possibles (2-3)
- Points d'attention
- Niveau de difficulté (1-5)
"""
    
    provider = list(llm_manager.clients.keys())[0]
    response = llm_manager.query_single_llm(
        provider,
        prompt,
        "Tu es un expert en préparation judiciaire. Génère des questions précises et pertinentes.",
        temperature=0.7,
        max_tokens=3000
    )
    
    if response['success']:
        # Parser les questions
        return parse_session_questions(response['response'])
    
    # Questions par défaut si échec
    return generate_default_questions(theme, num_questions)

def generate_session_objectives(theme: str, config: dict) -> List[str]:
    """Génère les objectifs pour une séance"""
    
    objectives_templates = {
        "Introduction et cadre juridique": [
            "Comprendre le cadre légal de la procédure",
            "Identifier ses droits et obligations",
            "Maîtriser le vocabulaire juridique essentiel",
            "Établir une relation de confiance avec l'avocat"
        ],
        "Travail sur le récit chronologique": [
            "Construire un récit cohérent et structuré",
            "Identifier les points de vigilance",
            "Mémoriser les dates et faits clés",
            "Éviter les contradictions"
        ],
        "Gestion des questions factuelles": [
            "Répondre précisément aux questions sur les faits",
            "Distinguer faits et interprétations",
            "Gérer les questions sur les détails",
            "Maintenir la cohérence"
        ],
        "Préparation aux questions pièges": [
            "Identifier les questions à double sens",
            "Éviter les admissions involontaires",
            "Maîtriser les techniques de reformulation",
            "Rester vigilant sur les présupposés"
        ],
        "Langage corporel et attitude": [
            "Adopter une posture appropriée",
            "Gérer les signes de stress",
            "Maintenir un contact visuel adapté",
            "Contrôler les gestes parasites"
        ],
        "Simulation complète": [
            "Mettre en pratique tous les apprentissages",
            "Identifier les derniers points d'amélioration",
            "Gagner en confiance",
            "Valider la stratégie globale"
        ]
    }
    
    # Adapter selon le profil
    base_objectives = objectives_templates.get(theme, [
        f"Maîtriser les aspects liés à : {theme}",
        "Progresser dans la préparation globale",
        "Renforcer la confiance",
        "Identifier et corriger les points faibles"
    ])
    
    # Ajouter des objectifs spécifiques au profil
    if config['profil_client'] == 'anxieux':
        base_objectives.append("Pratiquer des techniques de gestion du stress")
    elif config['profil_client'] == 'agressif':
        base_objectives.append("Canaliser l'énergie et éviter les confrontations")
    
    return base_objectives

def generate_session_exercises(theme: str, profile: str, focus_areas: List[str]) -> List[Dict[str, Any]]:
    """Génère des exercices adaptés pour une séance"""
    
    exercises = []
    
    # Exercices de base selon le thème
    theme_exercises = {
        "Gestion du stress": [
            {
                "title": "Respiration carrée",
                "description": "Technique de respiration 4-4-4-4 pour calmer l'anxiété",
                "duration": 5,
                "type": "relaxation"
            },
            {
                "title": "Ancrage sensoriel",
                "description": "Se concentrer sur 5 choses visibles, 4 sons, 3 sensations...",
                "duration": 10,
                "type": "mindfulness"
            }
        ],
        "Cohérence du récit": [
            {
                "title": "Timeline visuelle",
                "description": "Créer une frise chronologique des événements",
                "duration": 20,
                "type": "organization"
            },
            {
                "title": "Récit en 3 minutes",
                "description": "Raconter les faits essentiels en temps limité",
                "duration": 15,
                "type": "practice"
            }
        ],
        "Questions techniques": [
            {
                "title": "Glossaire personnel",
                "description": "Créer des définitions simples des termes techniques",
                "duration": 15,
                "type": "study"
            },
            {
                "title": "Vulgarisation",
                "description": "Expliquer un concept technique simplement",
                "duration": 10,
                "type": "communication"
            }
        ]
    }
    
    # Ajouter les exercices pertinents
    for area in focus_areas:
        if area in theme_exercises:
            exercises.extend(theme_exercises[area])
    
    # Exercices spécifiques au profil
    profile_exercises = {
        "anxieux": {
            "title": "Journal des pensées",
            "description": "Noter et restructurer les pensées anxiogènes",
            "duration": 15,
            "type": "cognitive"
        },
        "agressif": {
            "title": "Pause réflexive",
            "description": "S'entraîner à marquer des pauses avant de répondre",
            "duration": 10,
            "type": "control"
        },
        "fragile": {
            "title": "Affirmations positives",
            "description": "Répéter des phrases de renforcement",
            "duration": 5,
            "type": "confidence"
        }
    }
    
    if profile in profile_exercises:
        exercises.append(profile_exercises[profile])
    
    return exercises[:5]  # Limiter à 5 exercices par séance

def extract_key_points_for_session(theme: str, content: str) -> List[str]:
    """Extrait les points clés pertinents pour une séance"""
    
    # Extraire la section pertinente du contenu
    relevant_section = extract_section(content, theme)
    
    if not relevant_section:
        # Points clés génériques
        return [
            f"Maîtriser les aspects essentiels de : {theme}",
            "Rester cohérent avec la stratégie globale",
            "Pratiquer les réponses types",
            "Identifier ses points de vigilance personnels"
        ]
    
    # Extraire les points clés
    key_points = []
    
    # Chercher les éléments importants
    lines = relevant_section.split('\n')
    for line in lines:
        line = line.strip()
        if any(marker in line for marker in ['Important:', 'Essentiel:', 'Clé:', 'Retenir:']):
            key_points.append(line)
        elif line.startswith('•') or line.startswith('-'):
            if len(line) > 10 and len(key_points) < 6:
                key_points.append(line[1:].strip())
    
    return key_points[:5]

def generate_homework(session_num: int, theme: str, config: dict) -> str:
    """Génère les devoirs entre les séances"""
    
    homework_templates = {
        1: "Relire ses droits et créer une fiche récapitulative personnelle",
        2: "Établir une chronologie détaillée des événements sur papier",
        3: "S'enregistrer en train de répondre aux questions principales",
        4: "Identifier 5 questions pièges potentielles et préparer les parades",
        5: "Pratiquer devant un miroir pendant 15 minutes",
        6: "Faire une simulation complète avec un proche",
        7: "Réviser tous les points clés et se reposer"
    }
    
    base_homework = homework_templates.get(session_num, f"Réviser les points de la séance {session_num}")
    
    # Adapter selon le profil
    if config['profil_client'] == 'anxieux':
        base_homework += " + 10 minutes de relaxation quotidienne"
    elif config['profil_client'] == 'technique':
        base_homework += " + créer des fiches techniques"
    
    return base_homework

def parse_session_questions(response_text: str) -> List[Dict[str, str]]:
    """Parse les questions générées par l'IA"""
    
    questions = []
    current_question = {}
    
    lines = response_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if re.match(r'^\d+\..*Question|^Question \d+', line):
            # Nouvelle question
            if current_question:
                questions.append(current_question)
            current_question = {
                'question': re.sub(r'^\d+\.|^Question \d+:?\s*', '', line).strip(),
                'answer': '',
                'variants': [],
                'attention_points': '',
                'difficulty': 3
            }
        elif 'Réponse' in line or line.startswith('R:'):
            current_question['answer'] = re.sub(r'^R:|Réponse:?\s*', '', line).strip()
        elif 'Variante' in line:
            variant = re.sub(r'Variante \d+:?\s*', '', line).strip()
            current_question['variants'].append(variant)
        elif 'Attention' in line or 'Point' in line:
            current_question['attention_points'] = line
        elif 'Difficulté' in line:
            match = re.search(r'\d', line)
            if match:
                current_question['difficulty'] = int(match.group())
    
    if current_question:
        questions.append(current_question)
    
    return questions

def generate_default_questions(theme: str, num_questions: int) -> List[Dict[str, str]]:
    """Génère des questions par défaut pour une séance"""
    
    default_questions = []
    
    base_questions = {
        "Introduction et cadre juridique": [
            "Pouvez-vous me confirmer votre identité complète ?",
            "Comprenez-vous la nature de cette procédure ?",
            "Souhaitez-vous la présence de votre avocat ?"
        ],
        "Travail sur le récit chronologique": [
            "Pouvez-vous me raconter les faits dans l'ordre ?",
            "Où étiez-vous le [date] ?",
            "Qui était présent lors de ces événements ?"
        ]
    }
    
    # Utiliser les questions de base ou générer des génériques
    if theme in base_questions:
        questions = base_questions[theme]
    else:
        questions = [f"Question type {i+1} sur {theme}" for i in range(num_questions)]
    
    # Formatter
    for i, q in enumerate(questions[:num_questions]):
        default_questions.append({
            'question': q,
            'answer': "Réponse à préparer selon le cas spécifique",
            'variants': [],
            'attention_points': "Point d'attention à définir",
            'difficulty': 3
        })
    
    return default_questions

def display_preparation_plan_overview(plan: PreparationPlan):
    """Affiche un aperçu visuel du plan de préparation"""
    
    st.success("✅ Plan de préparation créé avec succès!")
    
    # Métriques générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 Nombre de séances", plan.total_sessions)
    
    with col2:
        total_hours = sum(s.duration_minutes for s in plan.sessions) / 60
        st.metric("⏱️ Durée totale", f"{total_hours:.1f} heures")
    
    with col3:
        if plan.target_date:
            days_remaining = (plan.target_date - datetime.now().date()).days
            st.metric("📆 Jours restants", days_remaining)
    
    with col4:
        total_questions = sum(len(s.questions) for s in plan.sessions)
        st.metric("❓ Questions totales", total_questions)
    
    # Visualisation du planning
    st.markdown("### 📊 Vue d'ensemble du programme")
    
    # Créer un graphique Gantt simple
    fig = create_preparation_gantt(plan)
    st.plotly_chart(fig, use_container_width=True)
    
    # Aperçu des séances
    st.markdown("### 📋 Résumé des séances")
    
    for session in plan.sessions[:3]:  # Montrer les 3 premières
        with st.expander(f"{session.title} ({session.duration_minutes} min)", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Objectifs:**")
                for obj in session.objectives[:3]:
                    st.write(f"• {obj}")
                
                st.markdown(f"**Questions prévues:** {len(session.questions)}")
                st.markdown(f"**Exercices:** {len(session.exercises)}")
            
            with col2:
                if session.homework:
                    st.info(f"📝 Devoir: {session.homework}")
    
    if plan.total_sessions > 3:
        st.info(f"... et {plan.total_sessions - 3} autres séances")
    
    # Actions
    st.markdown("### 🎯 Actions disponibles")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Exporter le plan complet", key="export_full_plan"):
            export_content = export_preparation_plan(plan)
            st.download_button(
                "💾 Télécharger plan PDF",
                export_content,
                f"plan_preparation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "application/pdf",
                key="download_plan"
            )
    
    with col2:
        if st.button("📅 Ajouter au calendrier", key="add_to_calendar"):
            calendar_data = create_calendar_entries(plan)
            st.download_button(
                "💾 Fichier calendrier (.ics)",
                calendar_data,
                f"seances_preparation_{datetime.now().strftime('%Y%m%d')}.ics",
                "text/calendar",
                key="download_calendar"
            )
    
    with col3:
        if st.button("📱 Version mobile", key="mobile_plan"):
            mobile_content = create_mobile_plan(plan)
            st.download_button(
                "💾 Plan mobile",
                mobile_content,
                f"plan_mobile_{datetime.now().strftime('%Y%m%d')}.txt",
                "text/plain",
                key="download_mobile_plan"
            )
    
    with col4:
        if st.button("▶️ Commencer la séance 1", key="start_session_1"):
            st.session_state.current_session = 1
            st.rerun()

def create_preparation_gantt(plan: PreparationPlan) -> go.Figure:
    """Crée un diagramme de Gantt pour le plan de préparation"""
    
    # Calculer les dates des séances
    if plan.target_date:
        days_available = (plan.target_date - datetime.now().date()).days
        interval = days_available / (plan.total_sessions + 1)
    else:
        interval = 4  # 4 jours par défaut entre séances
    
    # Préparer les données
    tasks = []
    for i, session in enumerate(plan.sessions):
        start_date = datetime.now() + timedelta(days=int(interval * i))
        end_date = start_date + timedelta(hours=session.duration_minutes/60)
        
        tasks.append({
            'Task': session.title,
            'Start': start_date,
            'Finish': end_date,
            'Complete': 100 if session.completed else 0,
            'Resource': f"Séance {i+1}"
        })
    
    # Créer le graphique
    fig = px.timeline(
        tasks,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Complete",
        title="Planning des séances de préparation",
        color_continuous_scale=["#ff9999", "#99ff99"]
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="",
        showlegend=False
    )
    
    return fig

def display_sessions_management(plan: PreparationPlan):
    """Interface de gestion des séances"""
    
    st.markdown("### 📅 Gestion des séances")
    
    # Sélection de la séance
    session_options = [f"{s.title}" for s in plan.sessions]
    selected_session_idx = st.selectbox(
        "Choisir une séance",
        range(len(session_options)),
        format_func=lambda x: session_options[x],
        key="session_selector"
    )
    
    session = plan.sessions[selected_session_idx]
    
    # Affichage détaillé de la séance
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"## {session.title}")
    
    with col2:
        if session.completed:
            st.success(f"✅ Complétée le {session.completion_date.strftime('%d/%m')}")
        else:
            st.warning("⏳ En attente")
    
    # Onglets pour la séance
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Vue d'ensemble",
        "❓ Questions",
        "🎯 Exercices",
        "📝 Notes",
        "📊 Évaluation"
    ])
    
    with tab1:
        display_session_overview(session)
    
    with tab2:
        display_session_questions(session)
    
    with tab3:
        display_session_exercises(session)
    
    with tab4:
        display_session_notes(session, selected_session_idx)
    
    with tab5:
        if session.completed:
            display_session_evaluation(session)
        else:
            complete_session_interface(session, selected_session_idx, plan)

def display_session_overview(session: PreparationSession):
    """Affiche la vue d'ensemble d'une séance"""
    
    # Informations générales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("⏱️ Durée", f"{session.duration_minutes} minutes")
    
    with col2:
        st.metric("❓ Questions", len(session.questions))
    
    with col3:
        st.metric("🎯 Exercices", len(session.exercises))
    
    # Objectifs
    st.markdown("### 🎯 Objectifs de la séance")
    for obj in session.objectives:
        st.write(f"✓ {obj}")
    
    # Points clés
    if session.key_points:
        st.markdown("### 📌 Points clés à retenir")
        for point in session.key_points:
            st.info(point)
    
    # Devoir
    if session.homework:
        st.markdown("### 📝 Travail personnel")
        st.warning(f"À faire avant la prochaine séance : {session.homework}")

def display_session_questions(session: PreparationSession):
    """Affiche et gère les questions d'une séance"""
    
    st.markdown(f"### ❓ {len(session.questions)} questions pour cette séance")
    
    # Options de filtrage
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Rechercher une question",
            placeholder="Ex: date, intention, preuve...",
            key=f"search_q_session_{session.session_number}"
        )
    
    with col2:
        difficulty_filter = st.select_slider(
            "Difficulté",
            options=["Toutes", 1, 2, 3, 4, 5],
            value="Toutes",
            key=f"diff_filter_{session.session_number}"
        )
    
    # Filtrer les questions
    filtered_questions = session.questions
    
    if search_term:
        filtered_questions = [
            q for q in filtered_questions
            if search_term.lower() in q['question'].lower() 
            or search_term.lower() in q.get('answer', '').lower()
        ]
    
    if difficulty_filter != "Toutes":
        filtered_questions = [
            q for q in filtered_questions
            if q.get('difficulty', 3) == difficulty_filter
        ]
    
    # Mode d'affichage
    display_mode = st.radio(
        "Mode d'affichage",
        ["Liste complète", "Mode pratique", "Flashcards"],
        horizontal=True,
        key=f"display_mode_{session.session_number}"
    )
    
    if display_mode == "Liste complète":
        # Affichage liste
        for i, q in enumerate(filtered_questions, 1):
            with st.expander(
                f"Q{i}: {q['question'][:80]}... (Difficulté: {'⭐' * q.get('difficulty', 3)})",
                expanded=False
            ):
                st.markdown("**Question complète:**")
                st.info(q['question'])
                
                st.markdown("**Réponse suggérée:**")
                st.success(q.get('answer', 'Réponse à définir'))
                
                if q.get('variants'):
                    st.markdown("**Variantes possibles:**")
                    for v in q['variants']:
                        st.write(f"• {v}")
                
                if q.get('attention_points'):
                    st.warning(f"⚠️ {q['attention_points']}")
    
    elif display_mode == "Mode pratique":
        # Mode pratique interactif
        if 'practice_index' not in st.session_state:
            st.session_state.practice_index = 0
        
        if filtered_questions:
            current_q = filtered_questions[st.session_state.practice_index % len(filtered_questions)]
            
            st.info(f"Question {st.session_state.practice_index + 1}/{len(filtered_questions)}")
            st.subheader(current_q['question'])
            
            user_answer = st.text_area(
                "Votre réponse:",
                height=150,
                key=f"practice_answer_{session.session_number}_{st.session_state.practice_index}"
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("👁️ Voir la réponse", key=f"show_answer_{st.session_state.practice_index}"):
                    st.success(current_q.get('answer', 'Pas de réponse suggérée'))
            
            with col2:
                if st.button("➡️ Question suivante", key=f"next_q_{st.session_state.practice_index}"):
                    st.session_state.practice_index += 1
                    st.rerun()
            
            with col3:
                if st.button("🔄 Recommencer", key=f"restart_practice_{session.session_number}"):
                    st.session_state.practice_index = 0
                    st.rerun()
    
    else:  # Flashcards
        # Mode flashcards
        if filtered_questions:
            if 'flashcard_index' not in st.session_state:
                st.session_state.flashcard_index = 0
            
            current_q = filtered_questions[st.session_state.flashcard_index % len(filtered_questions)]
            
            # Carte de question
            st.markdown(
                f"""
                <div style="
                    border: 2px solid #1f77b4;
                    border-radius: 10px;
                    padding: 30px;
                    text-align: center;
                    min-height: 200px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                ">
                    <h3>{current_q['question']}</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Contrôles
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("⬅️ Précédente", key="prev_flash"):
                    st.session_state.flashcard_index -= 1
                    st.rerun()
            
            with col2:
                if st.button("🔄 Retourner", key="flip_flash"):
                    with st.expander("Réponse", expanded=True):
                        st.success(current_q.get('answer', 'Pas de réponse'))
            
            with col3:
                if st.button("➡️ Suivante", key="next_flash"):
                    st.session_state.flashcard_index += 1
                    st.rerun()

def display_session_exercises(session: PreparationSession):
    """Affiche et gère les exercices d'une séance"""
    
    st.markdown(f"### 🎯 {len(session.exercises)} exercices")
    
    for i, exercise in enumerate(session.exercises, 1):
        with st.expander(f"Exercice {i}: {exercise['title']}", expanded=True):
            # Type d'exercice
            exercise_icons = {
                'relaxation': '😌',
                'practice': '🎯',
                'organization': '📊',
                'communication': '💬',
                'cognitive': '🧠',
                'mindfulness': '🧘',
                'study': '📚',
                'control': '🎮',
                'confidence': '💪'
            }
            
            icon = exercise_icons.get(exercise.get('type', 'general'), '📝')
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"{icon} **Type:** {exercise.get('type', 'général').title()}")
                st.write(exercise['description'])
            
            with col2:
                st.metric("⏱️ Durée", f"{exercise.get('duration', 10)} min")
            
            # Bouton pour commencer l'exercice
            if st.button(f"▶️ Commencer", key=f"start_ex_{session.session_number}_{i}"):
                start_exercise_session(exercise, session.session_number, i)

def display_session_notes(session: PreparationSession, session_idx: int):
    """Gère les notes pour une séance"""
    
    st.markdown("### 📝 Notes de séance")
    
    # Récupérer les notes existantes
    notes_key = f"session_notes_{session_idx}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = session.notes
    
    # Éditeur de notes
    new_notes = st.text_area(
        "Vos notes personnelles",
        value=st.session_state[notes_key],
        height=300,
        placeholder="Notez ici vos observations, difficultés rencontrées, points à revoir...",
        key=f"notes_editor_{session_idx}"
    )
    
    # Sauvegarder
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Sauvegarder les notes", key=f"save_notes_{session_idx}"):
            st.session_state[notes_key] = new_notes
            session.notes = new_notes
            st.success("Notes sauvegardées!")
    
    with col2:
        if st.button("📋 Modèle de notes", key=f"template_notes_{session_idx}"):
            template = """## Points forts de la séance
- 

## Difficultés rencontrées
- 

## Questions à approfondir
- 

## Actions pour la prochaine fois
- 

## Remarques personnelles
"""
            st.session_state[notes_key] = template
            st.rerun()

def complete_session_interface(session: PreparationSession, session_idx: int, plan: PreparationPlan):
    """Interface pour marquer une séance comme complétée"""
    
    st.markdown("### 📊 Compléter la séance")
    
    st.info("Évaluez votre performance pour cette séance")
    
    # Auto-évaluation
    col1, col2 = st.columns(2)
    
    with col1:
        overall_score = st.select_slider(
            "Score global",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: f"{x}/5 ⭐",
            key=f"overall_score_{session_idx}"
        )
        
        confidence_level = st.select_slider(
            "Niveau de confiance",
            options=["Très faible", "Faible", "Moyen", "Bon", "Excellent"],
            value="Moyen",
            key=f"confidence_{session_idx}"
        )
    
    with col2:
        objectives_met = st.multiselect(
            "Objectifs atteints",
            session.objectives,
            default=session.objectives[:2],
            key=f"objectives_met_{session_idx}"
        )
        
        needs_review = st.checkbox(
            "Cette séance nécessite une révision",
            key=f"needs_review_{session_idx}"
        )
    
    # Commentaires
    session_feedback = st.text_area(
        "Commentaires sur la séance",
        placeholder="Points positifs, difficultés, remarques...",
        key=f"feedback_{session_idx}"
    )
    
    # Valider la séance
    if st.button("✅ Valider et terminer la séance", key=f"complete_{session_idx}", type="primary"):
        # Mettre à jour la séance
        session.completed = True
        session.completion_date = datetime.now()
        session.score = overall_score / 5.0
        
        # Mettre à jour la progression globale
        completed_sessions = sum(1 for s in plan.sessions if s.completed)
        plan.overall_progress = completed_sessions / plan.total_sessions
        
        # Sauvegarder le feedback
        if 'session_feedback' not in st.session_state:
            st.session_state.session_feedback = {}
        
        st.session_state.session_feedback[session_idx] = {
            'score': overall_score,
            'confidence': confidence_level,
            'objectives_met': objectives_met,
            'needs_review': needs_review,
            'feedback': session_feedback
        }
        
        st.success(f"✅ Séance {session.session_number} complétée!")
        st.balloons()
        
        # Proposer la séance suivante
        if session_idx < len(plan.sessions) - 1:
            if st.button(f"➡️ Passer à la séance {session_idx + 2}", key="next_session"):
                st.session_state.current_session = session_idx + 2
                st.rerun()

def display_session_evaluation(session: PreparationSession):
    """Affiche l'évaluation d'une séance complétée"""
    
    st.markdown("### ✅ Séance complétée")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score", f"{session.score*5:.1f}/5 ⭐" if session.score else "N/A")
    
    with col2:
        st.metric("Date", session.completion_date.strftime("%d/%m/%Y") if session.completion_date else "N/A")
    
    with col3:
        feedback_key = f"session_feedback.{session.session_number-1}"
        if feedback_key in st.session_state:
            feedback = st.session_state[feedback_key]
            st.metric("Confiance", feedback.get('confidence', 'N/A'))
    
    # Détails de l'évaluation
    if f"session_feedback.{session.session_number-1}" in st.session_state:
        feedback = st.session_state[f"session_feedback.{session.session_number-1}"]
        
        with st.expander("📊 Détails de l'évaluation", expanded=True):
            st.write(f"**Objectifs atteints:** {len(feedback.get('objectives_met', []))}/{len(session.objectives)}")
            
            if feedback.get('needs_review'):
                st.warning("⚠️ Cette séance nécessite une révision")
            
            if feedback.get('feedback'):
                st.info(f"**Commentaires:** {feedback['feedback']}")

def display_progress_tracking(plan: PreparationPlan):
    """Affiche le suivi de progression global"""
    
    st.markdown("### 📊 Suivi de progression")
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    
    completed_sessions = sum(1 for s in plan.sessions if s.completed)
    total_score = sum(s.score for s in plan.sessions if s.completed and s.score) or 0
    avg_score = (total_score / completed_sessions * 5) if completed_sessions > 0 else 0
    
    with col1:
        st.metric(
            "Progression",
            f"{plan.overall_progress*100:.0f}%",
            f"{completed_sessions}/{plan.total_sessions} séances"
        )
    
    with col2:
        st.metric("Score moyen", f"{avg_score:.1f}/5 ⭐")
    
    with col3:
        if plan.target_date:
            days_left = (plan.target_date - datetime.now().date()).days
            st.metric("Jours restants", days_left)
    
    with col4:
        total_practice = sum(
            len(s.questions) for s in plan.sessions if s.completed
        )
        st.metric("Questions pratiquées", total_practice)
    
    # Graphique de progression
    st.markdown("### 📈 Évolution des performances")
    
    # Créer le graphique
    fig = create_progress_chart(plan)
    st.plotly_chart(fig, use_container_width=True)
    
    # Analyse détaillée
    st.markdown("### 🔍 Analyse détaillée")
    
    tab1, tab2, tab3 = st.tabs(["Par séance", "Par thème", "Recommandations"])
    
    with tab1:
        display_progress_by_session(plan)
    
    with tab2:
        display_progress_by_theme(plan)
    
    with tab3:
        display_progress_recommendations(plan)

def create_progress_chart(plan: PreparationPlan) -> go.Figure:
    """Crée un graphique de progression"""
    
    # Préparer les données
    sessions_data = []
    for s in plan.sessions:
        if s.completed and s.score:
            sessions_data.append({
                'Session': f"S{s.session_number}",
                'Score': s.score * 5,
                'Date': s.completion_date.strftime("%d/%m") if s.completion_date else ""
            })
    
    if not sessions_data:
        # Graphique vide
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune séance complétée pour le moment",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
    else:
        # Créer le graphique
        fig = go.Figure()
        
        # Ligne de progression
        fig.add_trace(go.Scatter(
            x=[d['Session'] for d in sessions_data],
            y=[d['Score'] for d in sessions_data],
            mode='lines+markers',
            name='Score',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10)
        ))
        
        # Ligne de référence
        fig.add_hline(y=3, line_dash="dash", line_color="gray", 
                      annotation_text="Objectif minimum")
        
        fig.update_layout(
            title="Évolution des scores par séance",
            xaxis_title="Séances",
            yaxis_title="Score (/5)",
            yaxis_range=[0, 5.5],
            height=400
        )
    
    return fig

def display_progress_by_session(plan: PreparationPlan):
    """Affiche la progression par séance"""
    
    for session in plan.sessions:
        icon = "✅" if session.completed else "⏳"
        
        with st.expander(f"{icon} {session.title}", expanded=not session.completed):
            if session.completed:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Score", f"{session.score*5:.1f}/5" if session.score else "N/A")
                
                with col2:
                    st.metric("Date", session.completion_date.strftime("%d/%m/%Y"))
                
                with col3:
                    st.metric("Durée", f"{session.duration_minutes} min")
                
                # Feedback
                feedback_key = f"session_feedback.{session.session_number-1}"
                if feedback_key in st.session_state:
                    feedback = st.session_state[feedback_key]
                    if feedback.get('feedback'):
                        st.info(f"💭 {feedback['feedback']}")
            else:
                st.warning("Séance non complétée")
                
                # Estimation du temps nécessaire
                if plan.target_date:
                    days_left = (plan.target_date - datetime.now().date()).days
                    sessions_left = sum(1 for s in plan.sessions if not s.completed)
                    
                    if sessions_left > 0:
                        recommended_interval = days_left / sessions_left
                        st.info(f"💡 Recommandation : compléter une séance tous les {recommended_interval:.0f} jours")

def display_progress_by_theme(plan: PreparationPlan):
    """Analyse la progression par thème"""
    
    # Grouper les performances par type d'exercice
    theme_scores = defaultdict(list)
    
    for session in plan.sessions:
        if session.completed and session.score:
            # Analyser le thème principal
            theme_key = categorize_session_theme(session.theme)
            theme_scores[theme_key].append(session.score * 5)
    
    if theme_scores:
        # Créer un graphique radar
        categories = list(theme_scores.keys())
        values = [sum(scores)/len(scores) for scores in theme_scores.values()]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Performance'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            title="Performance par domaine",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Analyse textuelle
        st.markdown("### 💡 Points d'attention")
        
        for theme, scores in theme_scores.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 3:
                st.error(f"❌ **{theme}** : Performance insuffisante ({avg_score:.1f}/5)")
            elif avg_score < 4:
                st.warning(f"⚠️ **{theme}** : À améliorer ({avg_score:.1f}/5)")
            else:
                st.success(f"✅ **{theme}** : Bonne maîtrise ({avg_score:.1f}/5)")

def categorize_session_theme(theme: str) -> str:
    """Catégorise le thème d'une séance"""
    
    theme_lower = theme.lower()
    
    if any(word in theme_lower for word in ['droit', 'juridique', 'procédure']):
        return "Aspects juridiques"
    elif any(word in theme_lower for word in ['récit', 'chronologie', 'faits']):
        return "Construction du récit"
    elif any(word in theme_lower for word in ['question', 'piège', 'réponse']):
        return "Questions/Réponses"
    elif any(word in theme_lower for word in ['stress', 'attitude', 'comportement']):
        return "Gestion émotionnelle"
    elif any(word in theme_lower for word in ['simulation', 'pratique', 'exercice']):
        return "Mise en pratique"
    else:
        return "Autres aspects"

def display_progress_recommendations(plan: PreparationPlan):
    """Affiche des recommandations personnalisées"""
    
    st.markdown("### 🎯 Recommandations personnalisées")
    
    # Analyser la progression
    completed = sum(1 for s in plan.sessions if s.completed)
    total = plan.total_sessions
    progress_ratio = completed / total if total > 0 else 0
    
    # Calculer le score moyen
    scores = [s.score * 5 for s in plan.sessions if s.completed and s.score]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Recommandations selon la progression
    if progress_ratio < 0.3:
        st.info("""
        **📅 Phase initiale**
        - Établissez un rythme régulier de séances
        - Concentrez-vous sur les fondamentaux
        - Ne sautez pas les exercices de base
        """)
    elif progress_ratio < 0.7:
        st.info("""
        **🚀 Phase intermédiaire**
        - Intensifiez les simulations
        - Travaillez les points faibles identifiés
        - Commencez à chronométrer vos réponses
        """)
    else:
        st.info("""
        **🏁 Phase finale**
        - Focus sur la confiance et la fluidité
        - Révisez les points clés
        - Pratiquez la gestion du stress
        """)
    
    # Recommandations selon les scores
    if avg_score < 3:
        st.error("""
        **⚠️ Performance à améliorer**
        - Reprenez les séances avec scores faibles
        - Demandez un accompagnement renforcé
        - Augmentez le temps de pratique personnel
        """)
    elif avg_score < 4:
        st.warning("""
        **📈 Progression encourageante**
        - Continuez sur cette lancée
        - Approfondissez les points moyens
        - Variez les exercices
        """)
    else:
        st.success("""
        **🌟 Excellente progression**
        - Maintenez ce niveau
        - Aidez-vous des notes pour consolider
        - Préparez-vous mentalement au jour J
        """)
    
    # Prochaines actions
    st.markdown("### 📋 Actions recommandées")
    
    uncompleted = [s for s in plan.sessions if not s.completed]
    if uncompleted:
        next_session = uncompleted[0]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"**Prochaine séance :** {next_session.title}")
            if next_session.homework:
                st.warning(f"**N'oubliez pas :** {next_session.homework}")
        
        with col2:
            if st.button("▶️ Commencer", key="start_next_recommended"):
                st.session_state.current_session = next_session.session_number
                st.rerun()

def display_resources_library():
    """Affiche la bibliothèque de ressources"""
    
    st.markdown("### 📚 Bibliothèque de ressources")
    
    # Catégories de ressources
    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 Guides",
        "🎥 Vidéos",
        "📝 Modèles",
        "🔗 Liens utiles"
    ])
    
    with tab1:
        st.markdown("#### 📖 Guides de préparation")
        
        guides = [
            {
                "title": "Guide complet de l'audition libre",
                "description": "Tout savoir sur le déroulement d'une audition",
                "pages": 15,
                "difficulty": "Débutant"
            },
            {
                "title": "Maîtriser l'interrogatoire d'instruction",
                "description": "Techniques avancées face au juge",
                "pages": 25,
                "difficulty": "Avancé"
            },
            {
                "title": "Gérer son stress en procédure",
                "description": "Techniques de relaxation et préparation mentale",
                "pages": 10,
                "difficulty": "Tous niveaux"
            }
        ]
        
        for guide in guides:
            with st.expander(guide["title"]):
                st.write(guide["description"])
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"📄 {guide['pages']} pages")
                with col2:
                    st.info(f"🎯 {guide['difficulty']}")
                
                if st.button(f"📥 Télécharger", key=f"dl_{guide['title']}"):
                    st.info("Guide disponible dans la version complète")
    
    with tab2:
        st.markdown("#### 🎥 Vidéos de formation")
        
        videos = [
            "Les erreurs à éviter en audition",
            "Simulation d'interrogatoire commentée",
            "Techniques de communication non-verbale",
            "Gérer une confrontation difficile"
        ]
        
        for video in videos:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"▶️ {video}")
            with col2:
                st.button("Regarder", key=f"watch_{video}")
    
    with tab3:
        st.markdown("#### 📝 Modèles de documents")
        
        templates = [
            "Chronologie type à compléter",
            "Liste de vérification pré-audition",
            "Journal de préparation",
            "Fiche de révision rapide"
        ]
        
        for template in templates:
            if st.button(f"📄 {template}", key=f"template_{template}"):
                st.info("Modèle disponible dans la version complète")
    
    with tab4:
        st.markdown("#### 🔗 Liens et ressources utiles")
        
        links = {
            "Code de procédure pénale": "Articles sur les droits en garde à vue",
            "Ordre des avocats": "Trouver un avocat spécialisé",
            "Association d'aide aux victimes": "Soutien psychologique",
            "Guides officiels": "Publications du ministère de la Justice"
        }
        
        for title, description in links.items():
            st.write(f"• **{title}** : {description}")

def display_preparation_settings():
    """Paramètres de la préparation"""
    
    st.markdown("### ⚙️ Paramètres de préparation")
    
    # Notifications
    st.markdown("#### 🔔 Notifications et rappels")
    
    col1, col2 = st.columns(2)
    
    with col1:
        reminder_enabled = st.checkbox(
            "Activer les rappels de séance",
            value=True,
            key="reminder_enabled"
        )
        
        if reminder_enabled:
            reminder_time = st.time_input(
                "Heure des rappels",
                value=datetime.strptime("09:00", "%H:%M").time(),
                key="reminder_time"
            )
    
    with col2:
        progress_reports = st.checkbox(
            "Rapports de progression hebdomadaires",
            value=True,
            key="progress_reports"
        )
        
        motivation_messages = st.checkbox(
            "Messages de motivation",
            value=True,
            key="motivation_messages"
        )
    
    # Personnalisation
    st.markdown("#### 🎨 Personnalisation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_session_duration = st.select_slider(
            "Durée par défaut des séances",
            options=[60, 90, 120, 150, 180],
            value=120,
            format_func=lambda x: f"{x} minutes",
            key="default_duration"
        )
        
        difficulty_preference = st.radio(
            "Niveau de difficulté préféré",
            ["Progressif", "Constant", "Intensif"],
            key="difficulty_pref"
        )
    
    with col2:
        practice_mode = st.selectbox(
            "Mode de pratique par défaut",
            ["Questions écrites", "Simulation orale", "Mixte"],
            key="practice_mode"
        )
        
        feedback_detail = st.select_slider(
            "Niveau de détail des feedbacks",
            options=["Minimal", "Standard", "Détaillé", "Très détaillé"],
            value="Détaillé",
            key="feedback_detail"
        )
    
    # Export et sauvegarde
    st.markdown("#### 💾 Export et sauvegarde")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Exporter toutes les données", key="export_all_data"):
            export_data = export_all_preparation_data()
            st.download_button(
                "💾 Télécharger l'export",
                export_data,
                f"preparation_complete_{datetime.now().strftime('%Y%m%d')}.json",
                "application/json",
                key="download_export"
            )
    
    with col2:
        if st.button("🔄 Synchroniser", key="sync_data"):
            st.success("✅ Données synchronisées")
    
    with col3:
        if st.button("🗑️ Réinitialiser", key="reset_data"):
            if st.checkbox("Confirmer la réinitialisation"):
                st.session_state.clear()
                st.success("✅ Données réinitialisées")
                st.rerun()

def start_exercise_session(exercise: Dict[str, Any], session_num: int, exercise_num: int):
    """Démarre une session d'exercice"""
    
    st.session_state.active_exercise = {
        'exercise': exercise,
        'session_num': session_num,
        'exercise_num': exercise_num,
        'start_time': datetime.now()
    }
    
    # Interface selon le type d'exercice
    if exercise['type'] == 'relaxation':
        show_relaxation_exercise(exercise)
    elif exercise['type'] == 'practice':
        show_practice_exercise(exercise)
    elif exercise['type'] == 'organization':
        show_organization_exercise(exercise)
    else:
        show_generic_exercise(exercise)

def show_relaxation_exercise(exercise: Dict[str, Any]):
    """Affiche un exercice de relaxation"""
    
    st.markdown(f"### 😌 {exercise['title']}")
    
    # Instructions
    st.info(exercise['description'])
    
    # Timer
    duration = exercise.get('duration', 5) * 60  # Convertir en secondes
    
    if 'exercise_timer' not in st.session_state:
        st.session_state.exercise_timer = duration
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Démarrer", key="start_relax"):
            st.session_state.exercise_running = True
    
    with col2:
        if st.button("⏸️ Pause", key="pause_relax"):
            st.session_state.exercise_running = False
    
    with col3:
        if st.button("🔄 Réinitialiser", key="reset_relax"):
            st.session_state.exercise_timer = duration
    
    # Affichage du timer
    if 'exercise_running' in st.session_state and st.session_state.exercise_running:
        remaining = st.session_state.exercise_timer
        mins, secs = divmod(remaining, 60)
        
        st.markdown(
            f"""
            <div style="text-align: center; font-size: 48px; font-weight: bold; color: #1f77b4;">
                {mins:02d}:{secs:02d}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Guide audio (simulé)
    with st.expander("🎧 Guide audio"):
        st.info("Guide audio disponible dans la version complète")

def show_practice_exercise(exercise: Dict[str, Any]):
    """Affiche un exercice de pratique"""
    
    st.markdown(f"### 🎯 {exercise['title']}")
    st.write(exercise['description'])
    
    # Zone de pratique
    practice_response = st.text_area(
        "Votre pratique:",
        height=200,
        placeholder="Commencez votre exercice ici...",
        key="practice_area"
    )
    
    # Chronomètre
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⏱️ Chronométrer", key="time_practice"):
            st.session_state.practice_start = datetime.now()
    
    with col2:
        if 'practice_start' in st.session_state:
            elapsed = (datetime.now() - st.session_state.practice_start).seconds
            st.metric("Temps écoulé", f"{elapsed}s")
    
    # Feedback
    if st.button("✅ Terminer et évaluer", key="evaluate_practice"):
        st.success("Exercice complété!")
        
        # Auto-évaluation
        st.markdown("#### Auto-évaluation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            performance = st.select_slider(
                "Performance",
                options=["À retravailler", "Correct", "Bien", "Excellent"],
                key="practice_performance"
            )
        
        with col2:
            difficulty = st.select_slider(
                "Difficulté ressentie",
                options=["Facile", "Modéré", "Difficile", "Très difficile"],
                key="practice_difficulty"
            )

def show_organization_exercise(exercise: Dict[str, Any]):
    """Affiche un exercice d'organisation"""
    
    st.markdown(f"### 📊 {exercise['title']}")
    st.write(exercise['description'])
    
    # Interface d'organisation
    st.markdown("#### Organisez vos idées")
    
    # Créer des zones pour organiser
    categories = ["Faits principaux", "Dates clés", "Personnes impliquées", "Preuves"]
    
    for category in categories:
        with st.expander(category, expanded=True):
            items = st.text_area(
                f"Listez les éléments pour {category}",
                height=100,
                key=f"org_{category}"
            )
    
    # Visualisation
    if st.button("📊 Créer une carte mentale", key="create_mindmap"):
        st.info("Fonctionnalité de carte mentale disponible dans la version complète")

def show_generic_exercise(exercise: Dict[str, Any]):
    """Affiche un exercice générique"""
    
    st.markdown(f"### 📝 {exercise['title']}")
    st.write(exercise['description'])
    
    # Instructions génériques
    st.info(f"⏱️ Durée recommandée : {exercise.get('duration', 10)} minutes")
    
    # Zone de travail
    work_area = st.text_area(
        "Espace de travail",
        height=300,
        placeholder="Utilisez cet espace pour votre exercice...",
        key="generic_work_area"
    )
    
    # Validation
    if st.button("✅ Marquer comme complété", key="complete_generic"):
        st.success("✅ Exercice complété!")

def export_preparation_plan(plan: PreparationPlan) -> bytes:
    """Exporte le plan de préparation complet"""
    
    # Créer le document
    content = f"""PLAN DE PRÉPARATION COMPLET
{'=' * 60}
Créé le : {plan.created_date.strftime('%d/%m/%Y')}
Type de procédure : {plan.prep_type}
Profil client : {plan.client_profile}
Stratégie : {plan.strategy}
Date cible : {plan.target_date.strftime('%d/%m/%Y') if plan.target_date else 'Non définie'}
Nombre de séances : {plan.total_sessions}
{'=' * 60}
"""
    
    # Ajouter chaque séance
    for session in plan.sessions:
        content += f"""
SÉANCE {session.session_number} : {session.title}
{'-' * 50}
Durée : {session.duration_minutes} minutes
Statut : {'Complétée' if session.completed else 'À faire'}
OBJECTIFS :
"""
        for obj in session.objectives:
            content += f"- {obj}\n"
        
        content += f"\nQUESTIONS ({len(session.questions)}) :\n"
        for i, q in enumerate(session.questions[:5], 1):
            content += f"{i}. {q['question']}\n"
            content += f"   → {q.get('answer', 'À définir')}\n"
        
        if len(session.questions) > 5:
            content += f"... et {len(session.questions) - 5} autres questions\n"
        
        content += f"\nEXERCICES :\n"
        for ex in session.exercises:
            content += f"- {ex['title']} ({ex.get('duration', 10)} min)\n"
        
        if session.homework:
            content += f"\nDEVOIR : {session.homework}\n"
        
        content += "\n" + "=" * 60 + "\n"
    
    return content.encode('utf-8')

def create_calendar_entries(plan: PreparationPlan) -> str:
    """Crée des entrées de calendrier au format iCal"""
    
    ical_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Preparation Client//FR
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""
    
    # Calculer les dates des séances
    if plan.target_date:
        days_available = (plan.target_date - datetime.now().date()).days
        interval = days_available / (plan.total_sessions + 1)
    else:
        interval = 4
    
    for i, session in enumerate(plan.sessions):
        start_date = datetime.now() + timedelta(days=int(interval * i))
        start_time = start_date.replace(hour=14, minute=0, second=0)  # 14h par défaut
        end_time = start_time + timedelta(minutes=session.duration_minutes)
        
        ical_content += f"""BEGIN:VEVENT
UID:{session.session_number}@preparationclient
DTSTART:{start_time.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_time.strftime('%Y%m%dT%H%M%S')}
SUMMARY:Préparation - {session.title}
DESCRIPTION:Séance {session.session_number} de préparation\\n{len(session.questions)} questions à préparer\\nDevoir: {session.homework or 'Aucun'}
LOCATION:Cabinet avocat
STATUS:CONFIRMED
END:VEVENT
"""
    
    ical_content += "END:VCALENDAR"
    
    return ical_content

def create_mobile_plan(plan: PreparationPlan) -> str:
    """Crée une version mobile du plan"""
    
    mobile_content = f"""PLAN MOBILE - {plan.prep_type.upper()}
{'=' * 40}
📅 {plan.total_sessions} SÉANCES
⏱️ {sum(s.duration_minutes for s in plan.sessions)} MIN TOTAL
🎯 STRATÉGIE: {plan.strategy.upper()}
{'=' * 40}
"""
    
    for s in plan.sessions:
        status = "✅" if s.completed else "⏳"
        mobile_content += f"""
{status} SÉANCE {s.session_number}
{s.theme}
⏱️ {s.duration_minutes} min
❓ {len(s.questions)} questions
📝 {s.homework or 'Pas de devoir'}
{'-' * 40}
"""
    
    # Ajouter les questions essentielles
    mobile_content += "\n❓ TOP QUESTIONS\n" + "=" * 40 + "\n"
    
    question_count = 0
    for session in plan.sessions:
        for q in session.questions[:2]:  # 2 questions par séance
            question_count += 1
            mobile_content += f"\nQ{question_count}: {q['question']}\n"
            mobile_content += f"→ {q.get('answer', 'À préparer')}\n"
            mobile_content += "-" * 40 + "\n"
    
    return mobile_content

def export_all_preparation_data() -> str:
    """Exporte toutes les données de préparation"""
    
    export_data = {
        'export_date': datetime.now().isoformat(),
        'version': '1.0'
    }
    
    # Plan de préparation
    if 'preparation_plan' in st.session_state:
        plan = st.session_state.preparation_plan
        export_data['preparation_plan'] = {
            'total_sessions': plan.total_sessions,
            'prep_type': plan.prep_type,
            'client_profile': plan.client_profile,
            'strategy': plan.strategy,
            'created_date': plan.created_date.isoformat(),
            'target_date': plan.target_date.isoformat() if plan.target_date else None,
            'overall_progress': plan.overall_progress,
            'sessions': []
        }
        
        for session in plan.sessions:
            session_data = {
                'session_number': session.session_number,
                'title': session.title,
                'theme': session.theme,
                'objectives': session.objectives,
                'duration_minutes': session.duration_minutes,
                'completed': session.completed,
                'completion_date': session.completion_date.isoformat() if session.completion_date else None,
                'score': session.score,
                'notes': session.notes,
                'questions_count': len(session.questions),
                'exercises_count': len(session.exercises)
            }
            export_data['preparation_plan']['sessions'].append(session_data)
    
    # Résultats de préparation
    if 'preparation_client_result' in st.session_state:
        result = st.session_state.preparation_client_result
        export_data['preparation_result'] = {
            'prep_type': result.prep_type,
            'profile': result.profile,
            'strategy': result.strategy,
            'timestamp': result.timestamp.isoformat(),
            'key_qa_count': len(result.key_qa),
            'do_not_say_count': len(result.do_not_say)
        }
    
    # Feedback des séances
    if 'session_feedback' in st.session_state:
        export_data['session_feedback'] = st.session_state.session_feedback
    
    # Notes
    notes_data = {}
    for key in st.session_state:
        if key.startswith('session_notes_'):
            notes_data[key] = st.session_state[key]
    
    if notes_data:
        export_data['notes'] = notes_data
    
    return json.dumps(export_data, ensure_ascii=False, indent=2)

# Classe étendue pour le résultat de préparation
class PreparationClientResult:
    def __init__(self, content, prep_type, profile, strategy, key_qa, 
                 do_not_say, exercises, duration_estimate, timestamp):
        self.content = content
        self.prep_type = prep_type
        self.profile = profile
        self.strategy = strategy
        self.key_qa = key_qa
        self.do_not_say = do_not_say
        self.exercises = exercises
        self.duration_estimate = duration_estimate
        self.timestamp = timestamp
    
    def get_top_questions(self, n=10):
        """Retourne les n questions les plus importantes"""
        return self.key_qa[:n]