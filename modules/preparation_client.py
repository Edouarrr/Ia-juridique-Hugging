# modules/preparation_client.py
"""Module de préparation des clients pour auditions et interrogatoires"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict

from config.app_config import LLMProvider
from managers.multi_llm_manager import MultiLLMManager
from models.dataclasses import PreparationClientResult
from utils.helpers import extract_section

def process_preparation_client_request(query: str, analysis: dict):
    """Traite une demande de préparation client"""
    
    st.markdown("### 👥 Préparation du client")
    
    # Configuration de la préparation
    config = display_preparation_config_interface(analysis)
    
    if st.button("🚀 Générer la préparation", key="generate_preparation", type="primary"):
        with st.spinner("📋 Génération de la préparation en cours..."):
            result = generate_client_preparation(config, analysis)
            
            if result:
                st.session_state.preparation_client_result = result
                display_preparation_results(result)

def display_preparation_config_interface(analysis: dict) -> dict:
    """Interface de configuration pour la préparation"""
    
    config = {}
    
    # Configuration en colonnes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Type de préparation
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
        
        # Profil du client
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
    
    with col2:
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
        
        # Niveau de détail
        config['niveau_detail'] = st.select_slider(
            "📊 Niveau de détail",
            options=["Essentiel", "Standard", "Approfondi", "Exhaustif"],
            value="Approfondi",
            key="niveau_detail_select"
        )
    
    with col3:
        # Options supplémentaires
        config['avec_simulation'] = st.checkbox(
            "🎮 Inclure simulation Q/R",
            value=True,
            help="Questions probables et réponses suggérées",
            key="avec_simulation_check"
        )
        
        config['avec_pieges'] = st.checkbox(
            "🚨 Identifier les pièges",
            value=True,
            help="Questions pièges et comment les éviter",
            key="avec_pieges_check"
        )
        
        config['avec_droits'] = st.checkbox(
            "⚖️ Rappel des droits",
            value=True,
            help="Droits du client selon la procédure",
            key="avec_droits_check"
        )
    
    # Éléments du dossier
    with st.expander("📂 Contexte de l'affaire", expanded=True):
        config['infractions'] = st.text_area(
            "⚖️ Infractions reprochées",
            value=analysis.get('infractions', ''),
            placeholder="Ex: Abus de biens sociaux, faux et usage de faux...",
            height=100,
            key="infractions_textarea"
        )
        
        config['elements_favorables'] = st.text_area(
            "✅ Éléments favorables",
            placeholder="- Absence de preuve directe\n- Témoignages favorables\n- Contexte atténuant",
            height=100,
            key="elements_favorables_textarea"
        )
        
        config['elements_defavorables'] = st.text_area(
            "❌ Éléments défavorables",
            placeholder="- Documents compromettants\n- Témoignages à charge\n- Aveux partiels",
            height=100,
            key="elements_defavorables_textarea"
        )
    
    # Points spécifiques à préparer
    config['points_sensibles'] = st.text_area(
        "🎯 Points sensibles à préparer",
        placeholder="- Explication des virements suspects\n- Justification des dépenses\n- Alibi pour certaines dates",
        height=100,
        key="points_sensibles_textarea"
    )
    
    return config

def generate_client_preparation(config: dict, analysis: dict) -> Optional[PreparationClientResult]:
    """Génère une préparation complète pour le client"""
    
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        st.error("❌ Aucune IA disponible")
        return None
    
    # Construire le prompt
    prompt = build_preparation_prompt(config, analysis)
    system_prompt = build_preparation_system_prompt(config)
    
    # Générer la préparation
    provider = list(llm_manager.clients.keys())[0]
    response = llm_manager.query_single_llm(
        provider,
        prompt,
        system_prompt,
        temperature=0.7,
        max_tokens=6000
    )
    
    if response['success']:
        content = response['response']
        
        # Extraire les éléments
        key_qa = extract_key_qa(content)
        do_not_say = extract_never_say(content)
        exercises = extract_preparation_exercises(content)
        
        # Estimer la durée
        duration_estimate = estimate_preparation_duration(config['prep_type'], config['niveau_detail'])
        
        return PreparationClientResult(
            content=content,
            prep_type=config['prep_type'],
            profile=config['profil_client'],
            strategy=config['strategie'],
            key_qa=key_qa,
            do_not_say=do_not_say,
            exercises=exercises,
            duration_estimate=duration_estimate,
            timestamp=datetime.now()
        )
    
    return None

def build_preparation_prompt(config: dict, analysis: dict) -> str:
    """Construit le prompt pour la préparation"""
    
    # Contexte selon le type
    type_context = {
        "audition": "audition libre en police/gendarmerie",
        "interrogatoire": "interrogatoire devant le juge d'instruction",
        "comparution": "comparution devant le tribunal",
        "confrontation": "confrontation avec d'autres parties",
        "expertise": "expertise psychiatrique ou psychologique"
    }
    
    prompt = f"""Crée une préparation complète pour un client qui va subir une {type_context.get(config['prep_type'], 'procédure')}.

PROFIL DU CLIENT:
- Type psychologique : {config['profil_client']}
- Stratégie adoptée : {config['strategie']}
- Niveau de détail souhaité : {config['niveau_detail']}

CONTEXTE DE L'AFFAIRE:
Infractions reprochées : {config.get('infractions', 'Non précisées')}

Éléments favorables :
{config.get('elements_favorables', 'À identifier')}

Éléments défavorables :
{config.get('elements_defavorables', 'À identifier')}

Points sensibles :
{config.get('points_sensibles', 'À préparer')}

LA PRÉPARATION DOIT INCLURE:

1. CONSEILS GÉNÉRAUX
   - Attitude et comportement
   - Tenue vestimentaire
   - Gestion du stress
   - Communication non-verbale

2. STRATÉGIE DE DÉFENSE
   - Ligne directrice
   - Points à mettre en avant
   - Points à éviter absolument
   - Cohérence du discours

3. QUESTIONS PROBABLES ET RÉPONSES
   - Questions sur les faits
   - Questions sur les intentions
   - Questions techniques
   - Questions pièges

4. CE QU'IL NE FAUT JAMAIS DIRE
   - Phrases à éviter
   - Admissions dangereuses
   - Contradictions à éviter
   - Formulations risquées

5. GESTION DES MOMENTS DIFFICILES
   - Si déstabilisé
   - Si confronté à une preuve
   - Si contradiction détectée
   - Si pression excessive
"""
    
    # Adaptations selon le profil
    profile_adaptations = {
        "anxieux": """
ADAPTATION CLIENT ANXIEUX:
- Techniques de respiration
- Phrases de recentrage
- Pauses stratégiques
- Reformulation pour gagner du temps
""",
        "confiant": """
ADAPTATION CLIENT CONFIANT:
- Éviter l'excès de confiance
- Rester vigilant
- Ne pas minimiser les enjeux
- Contrôler les déclarations spontanées
""",
        "agressif": """
ADAPTATION CLIENT AGRESSIF:
- Canaliser l'agressivité
- Éviter les confrontations
- Réponses courtes et factuelles
- Techniques de désamorçage
""",
        "fragile": """
ADAPTATION CLIENT FRAGILE:
- Renforcement positif
- Préparation aux questions difficiles
- Droit de demander des pauses
- Soutien psychologique
""",
        "technique": """
ADAPTATION CLIENT TECHNIQUE:
- Approche factuelle
- Précision des termes
- Documentation à l'appui
- Éviter sur-explication
"""
    }
    
    prompt += profile_adaptations.get(config['profil_client'], '')
    
    # Options spécifiques
    if config.get('avec_simulation'):
        prompt += """
6. SIMULATION QUESTIONS/RÉPONSES
   - 20-30 questions types avec réponses suggérées
   - Variantes selon les réponses de l'enquêteur
   - Points d'attention sur chaque réponse
"""
    
    if config.get('avec_pieges'):
        prompt += """
7. QUESTIONS PIÈGES ET PARADES
   - Questions à double sens
   - Questions présupposant des faits
   - Questions de déstabilisation
   - Techniques de parade
"""
    
    if config.get('avec_droits'):
        prompt += f"""
8. RAPPEL DES DROITS
   - Droits spécifiques à la {config['prep_type']}
   - Possibilités de refus
   - Assistance de l'avocat
   - Recours possibles
"""
    
    # Niveau de détail
    detail_instructions = {
        "Essentiel": "Document concis avec l'essentiel (5-8 pages)",
        "Standard": "Document standard équilibré (10-15 pages)",
        "Approfondi": "Document détaillé avec exemples (15-25 pages)",
        "Exhaustif": "Document exhaustif couvrant tous les cas (25+ pages)"
    }
    
    prompt += f"\nNIVEAU DE DÉTAIL: {detail_instructions.get(config['niveau_detail'], 'Standard')}"
    
    return prompt

def build_preparation_system_prompt(config: dict) -> str:
    """Construit le prompt système pour la préparation"""
    
    base_prompt = "Tu es un avocat pénaliste expérimenté, expert en préparation de clients pour les procédures pénales."
    
    # Spécialisation selon le type
    specializations = {
        "audition": "Tu maîtrises parfaitement les auditions de police et sais préparer les clients à cet exercice.",
        "interrogatoire": "Tu es spécialisé dans la préparation aux interrogatoires d'instruction.",
        "comparution": "Tu excelles dans la préparation des clients pour leur comparution devant le tribunal.",
        "confrontation": "Tu es expert en préparation aux confrontations, sachant gérer les dynamiques complexes.",
        "expertise": "Tu connais parfaitement les expertises judiciaires et leur déroulement."
    }
    
    base_prompt += f" {specializations.get(config['prep_type'], '')}"
    
    base_prompt += " Tu adoptes une approche pédagogique et bienveillante, tout en étant rigoureux sur la préparation."
    
    return base_prompt

def extract_key_qa(content: str) -> List[Dict[str, str]]:
    """Extrait les questions-réponses clés"""
    qa_list = []
    
    # Pattern pour Q/R
    qa_sections = re.split(r'(?=(?:Question|Q)\s*\d*\s*:)', content)
    
    for section in qa_sections[1:]:  # Skip le premier qui n'est pas une question
        lines = section.strip().split('\n')
        
        if len(lines) >= 2:
            # Extraire la question
            question = re.sub(r'^(?:Question|Q)\s*\d*\s*:\s*', '', lines[0]).strip()
            
            # Chercher la réponse
            answer = ""
            for i, line in enumerate(lines[1:]):
                if re.match(r'^(?:Réponse|R)\s*:', line):
                    # Réponse explicite
                    answer = re.sub(r'^(?:Réponse|R)\s*:\s*', '', line).strip()
                    # Continuer pour les lignes suivantes
                    for j in range(i+2, len(lines)):
                        if lines[j].strip() and not re.match(r'^(?:Question|Q|Attention|Note)', lines[j]):
                            answer += " " + lines[j].strip()
                        else:
                            break
                    break
                elif line.strip() and not re.match(r'^(?:Attention|Note|Point)', line):
                    # Considérer comme partie de la réponse
                    answer += line.strip() + " "
            
            if question and answer:
                qa_list.append({
                    'question': question,
                    'answer': answer.strip()
                })
    
    return qa_list

def extract_never_say(content: str) -> List[str]:
    """Extrait les choses à ne jamais dire"""
    never_list = []
    
    # Chercher la section
    sections = re.split(r'(?=\d+\.\s+[A-Z]|[IVX]+\.\s+[A-Z])', content)
    
    for section in sections:
        if any(phrase in section.upper() for phrase in ['NE JAMAIS', 'ÉVITER', 'NE PAS DIRE']):
            # Extraire les éléments
            items = re.findall(r'[-•]\s*([^\n]+)', section)
            never_list.extend(items)
            
            # Aussi chercher les phrases entre guillemets
            quoted = re.findall(r'"([^"]+)"', section)
            never_list.extend(quoted)
    
    # Dédupliquer et nettoyer
    cleaned_list = []
    seen = set()
    
    for item in never_list:
        item = item.strip()
        if item and item.lower() not in seen and len(item) > 10:
            seen.add(item.lower())
            cleaned_list.append(item)
    
    return cleaned_list[:20]  # Limiter à 20

def extract_preparation_exercises(content: str) -> List[Dict[str, Any]]:
    """Extrait les exercices de préparation"""
    exercises = []
    
    # Patterns d'exercices
    exercise_keywords = ['exercice', 'entraînement', 'simulation', 'pratique', 'répétition']
    
    sections = content.split('\n\n')
    
    for section in sections:
        if any(keyword in section.lower() for keyword in exercise_keywords):
            lines = section.strip().split('\n')
            if lines:
                title = lines[0].strip()
                description = '\n'.join(lines[1:]).strip()
                
                if len(description) > 20:
                    exercises.append({
                        'title': title,
                        'description': description,
                        'type': detect_exercise_type(title + description)
                    })
    
    return exercises

def detect_exercise_type(text: str) -> str:
    """Détecte le type d'exercice"""
    text_lower = text.lower()
    
    if 'respiration' in text_lower or 'stress' in text_lower:
        return 'relaxation'
    elif 'question' in text_lower or 'réponse' in text_lower:
        return 'qa_practice'
    elif 'reformulation' in text_lower:
        return 'reformulation'
    elif 'silence' in text_lower:
        return 'silence_management'
    else:
        return 'general'

def estimate_preparation_duration(prep_type: str, niveau_detail: str) -> str:
    """Estime la durée de préparation nécessaire"""
    
    # Durées de base par type
    base_durations = {
        "audition": 2,
        "interrogatoire": 3,
        "comparution": 4,
        "confrontation": 3,
        "expertise": 2
    }
    
    # Multiplicateurs par niveau
    detail_multipliers = {
        "Essentiel": 0.7,
        "Standard": 1.0,
        "Approfondi": 1.5,
        "Exhaustif": 2.0
    }
    
    base_hours = base_durations.get(prep_type, 3)
    multiplier = detail_multipliers.get(niveau_detail, 1.0)
    
    total_hours = int(base_hours * multiplier)
    
    if total_hours <= 2:
        return f"{total_hours} heure{'s' if total_hours > 1 else ''}"
    else:
        sessions = (total_hours + 1) // 2  # Sessions de 2h max
        return f"{total_hours} heures (en {sessions} sessions)"

def display_preparation_results(result: PreparationClientResult):
    """Affiche les résultats de la préparation"""
    
    st.success("✅ Préparation générée avec succès!")
    
    # Métadonnées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        type_icons = {
            "audition": "👮",
            "interrogatoire": "👨‍⚖️",
            "comparution": "⚖️",
            "confrontation": "🤝",
            "expertise": "🔬"
        }
        st.metric("Type", f"{type_icons.get(result.prep_type, '📋')} {result.prep_type.title()}")
    
    with col2:
        st.metric("Profil client", result.profile.title())
    
    with col3:
        st.metric("Stratégie", result.strategy.title())
    
    with col4:
        st.metric("Durée préparation", result.duration_estimate)
    
    # Navigation
    tabs = st.tabs([
        "📝 Document complet",
        "❓ Questions/Réponses",
        "🚫 À ne jamais dire",
        "🎯 Exercices",
        "📋 Fiche résumé"
    ])
    
    with tabs[0]:
        # Document complet
        display_full_preparation(result.content)
    
    with tabs[1]:
        # Questions/Réponses
        display_qa_section(result.key_qa)
    
    with tabs[2]:
        # À ne jamais dire
        display_never_say_section(result.do_not_say)
    
    with tabs[3]:
        # Exercices
        display_exercises_section(result.exercises)
    
    with tabs[4]:
        # Fiche résumé
        display_preparation_summary(result)
    
    # Actions
    st.markdown("### 💾 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Exporter PDF", key="export_prep_pdf"):
            pdf_content = export_preparation_to_pdf(result)
            st.download_button(
                "💾 Télécharger PDF",
                pdf_content,
                f"preparation_{result.prep_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "application/pdf",
                key="download_prep_pdf"
            )
    
    with col2:
        if st.button("🎮 Mode simulation", key="start_simulation"):
            st.session_state.simulation_active = True
            show_interrogation_simulation(result)
    
    with col3:
        if st.button("⏱️ Chronomètre", key="show_timer"):
            show_exercise_timer()
    
    with col4:
        if st.button("📱 Version mobile", key="mobile_version"):
            mobile_content = create_mobile_version(result)
            st.download_button(
                "💾 Version mobile",
                mobile_content.encode('utf-8'),
                f"prep_mobile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                key="download_mobile"
            )

def display_full_preparation(content: str):
    """Affiche le document complet de préparation"""
    
    # Options d'affichage
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "🔍 Rechercher dans le document",
            placeholder="Ex: stress, questions, droits...",
            key="search_prep_doc"
        )
    
    with col2:
        highlight = st.checkbox("🖍️ Surligner", value=True, key="highlight_prep")
    
    # Contenu avec recherche
    display_content = content
    
    if search_term and highlight:
        # Surligner les termes recherchés
        display_content = highlight_search_terms(content, search_term)
        
        # Compter les occurrences
        count = content.lower().count(search_term.lower())
        if count > 0:
            st.info(f"🔍 {count} occurrence(s) trouvée(s)")
    
    # Afficher avec scroll
    st.markdown(
        f'<div style="height: 600px; overflow-y: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">{display_content}</div>',
        unsafe_allow_html=True
    )

def display_qa_section(key_qa: List[Dict[str, str]]):
    """Affiche la section questions/réponses"""
    
    if not key_qa:
        st.info("Aucune question/réponse extraite")
        return
    
    st.markdown(f"### 📋 {len(key_qa)} questions préparées")
    
    # Filtres
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_qa = st.text_input(
            "🔍 Filtrer les questions",
            placeholder="Ex: intention, preuve, alibi...",
            key="search_qa"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Trier par",
            ["Ordre original", "Longueur question", "Longueur réponse"],
            key="sort_qa"
        )
    
    # Filtrer et trier
    filtered_qa = key_qa
    
    if search_qa:
        filtered_qa = [
            qa for qa in filtered_qa 
            if search_qa.lower() in qa['question'].lower() or search_qa.lower() in qa['answer'].lower()
        ]
    
    if sort_by == "Longueur question":
        filtered_qa.sort(key=lambda x: len(x['question']))
    elif sort_by == "Longueur réponse":
        filtered_qa.sort(key=lambda x: len(x['answer']))
    
    # Afficher
    for i, qa in enumerate(filtered_qa, 1):
        with st.expander(f"❓ Question {i}: {qa['question'][:60]}...", expanded=False):
            st.markdown("**Question complète:**")
            st.info(qa['question'])
            
            st.markdown("**Réponse suggérée:**")
            st.success(qa['answer'])
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 Copier", key=f"copy_qa_{i}"):
                    st.code(f"Q: {qa['question']}\nR: {qa['answer']}")
            
            with col2:
                if st.button("✏️ Noter", key=f"note_qa_{i}"):
                    note = st.text_area("Note personnelle", key=f"note_text_{i}")
                    if note:
                        if 'qa_notes' not in st.session_state:
                            st.session_state.qa_notes = {}
                        st.session_state.qa_notes[i] = note
            
            with col3:
                importance = st.select_slider(
                    "Importance",
                    options=["Faible", "Moyenne", "Haute", "Critique"],
                    value="Moyenne",
                    key=f"importance_qa_{i}"
                )

def display_never_say_section(never_say: List[str]):
    """Affiche la section des choses à ne jamais dire"""
    
    if not never_say:
        st.info("Aucune phrase à éviter identifiée")
        return
    
    st.markdown(f"### 🚫 {len(never_say)} phrases à éviter absolument")
    
    # Catégoriser les phrases
    categories = categorize_never_say(never_say)
    
    for category, phrases in categories.items():
        if phrases:
            with st.expander(f"⚠️ {category} ({len(phrases)} phrases)", expanded=True):
                for phrase in phrases:
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        st.error(f"❌ « {phrase} »")
                    
                    with col2:
                        if st.button("💡", key=f"explain_{hash(phrase)}"):
                            st.info(get_danger_explanation(phrase))

def categorize_never_say(phrases: List[str]) -> Dict[str, List[str]]:
    """Catégorise les phrases à éviter"""
    
    categories = {
        "Aveux implicites": [],
        "Contradictions": [],
        "Spéculations": [],
        "Accusations": [],
        "Minimisations excessives": [],
        "Autres": []
    }
    
    for phrase in phrases:
        phrase_lower = phrase.lower()
        
        if any(word in phrase_lower for word in ['avoue', 'reconnais', 'admets', 'coupable']):
            categories["Aveux implicites"].append(phrase)
        elif any(word in phrase_lower for word in ['mais', 'cependant', 'sauf', 'excepté']):
            categories["Contradictions"].append(phrase)
        elif any(word in phrase_lower for word in ['pense', 'crois', 'suppose', 'peut-être']):
            categories["Spéculations"].append(phrase)
        elif any(word in phrase_lower for word in ['lui', 'eux', 'elle', 'accusé']):
            categories["Accusations"].append(phrase)
        elif any(word in phrase_lower for word in ['peu', 'rien', 'jamais', 'insignifiant']):
            categories["Minimisations excessives"].append(phrase)
        else:
            categories["Autres"].append(phrase)
    
    return {k: v for k, v in categories.items() if v}

def get_danger_explanation(phrase: str) -> str:
    """Explique pourquoi une phrase est dangereuse"""
    
    phrase_lower = phrase.lower()
    
    if 'avoue' in phrase_lower or 'reconnais' in phrase_lower:
        return "Cette formulation constitue un aveu, même partiel. Préférez des formulations neutres."
    elif 'pense' in phrase_lower or 'crois' in phrase_lower:
        return "Évitez les spéculations. Restez factuel : 'Je sais' ou 'Je ne sais pas'."
    elif 'mais' in phrase_lower:
        return "Le 'mais' introduit souvent une contradiction. Soyez cohérent dans vos déclarations."
    else:
        return "Cette formulation peut être interprétée défavorablement. Restez neutre et factuel."

def display_exercises_section(exercises: List[Dict[str, Any]]):
    """Affiche la section des exercices"""
    
    if not exercises:
        st.info("Aucun exercice spécifique identifié")
        return
    
    st.markdown(f"### 🎯 {len(exercises)} exercices de préparation")
    
    # Grouper par type
    by_type = defaultdict(list)
    for ex in exercises:
        by_type[ex.get('type', 'general')].append(ex)
    
    type_names = {
        'relaxation': '😌 Relaxation',
        'qa_practice': '❓ Pratique Q/R',
        'reformulation': '🔄 Reformulation',
        'silence_management': '🤐 Gestion du silence',
        'general': '📋 Général'
    }
    
    for ex_type, type_exercises in by_type.items():
        st.markdown(f"#### {type_names.get(ex_type, ex_type.title())}")
        
        for i, exercise in enumerate(type_exercises, 1):
            with st.expander(f"🎯 {exercise['title']}", expanded=False):
                st.markdown(exercise['description'])
                
                # Bouton pour pratiquer
                if st.button(f"▶️ Pratiquer", key=f"practice_{ex_type}_{i}"):
                    show_exercise_practice(exercise)

def display_preparation_summary(result: PreparationClientResult):
    """Affiche une fiche résumé de la préparation"""
    
    summary = create_preparation_summary(result)
    
    # Afficher la fiche
    st.markdown("### 📋 Fiche résumé à imprimer")
    
    st.text_area(
        "Résumé de la préparation",
        value=summary,
        height=600,
        key="prep_summary_display"
    )
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "💾 Télécharger résumé",
            summary.encode('utf-8'),
            f"resume_preparation_{datetime.now().strftime('%Y%m%d')}.txt",
            "text/plain",
            key="download_prep_summary"
        )
    
    with col2:
        if st.button("🖨️ Format impression", key="print_format"):
            print_version = create_print_friendly_summary(result)
            st.download_button(
                "💾 Version impression",
                print_version.encode('utf-8'),
                f"fiche_preparation_{datetime.now().strftime('%Y%m%d')}.txt",
                "text/plain",
                key="download_print_version"
            )

def create_preparation_summary(result: PreparationClientResult) -> str:
    """Crée une fiche résumé de la préparation"""
    
    summary = f"""FICHE RÉSUMÉ - PRÉPARATION {result.prep_type.upper()}
{'=' * 60}

Date : {result.timestamp.strftime('%d/%m/%Y')}
Profil client : {result.profile}
Stratégie : {result.strategy}
Durée préparation : {result.duration_estimate}

POINTS CLÉS À RETENIR :
{'-' * 40}
"""
    
    # Top 10 Q/R
    summary += "\n📌 QUESTIONS ESSENTIELLES :\n\n"
    
    for i, qa in enumerate(result.get_top_questions(10), 1):
        summary += f"{i}. Q: {qa['question']}\n"
        summary += f"   R: {qa['answer']}\n\n"
    
    # Phrases à éviter absolument
    summary += "\n⚠️ NE JAMAIS DIRE :\n"
    summary += "-" * 40 + "\n"
    
    for item in result.do_not_say[:10]:
        summary += f"❌ {item}\n"
    
    # Conseils comportement
    behavior_section = extract_section(result.content, "COMPORTEMENT")
    if behavior_section:
        summary += f"\n💡 COMPORTEMENT :\n{'-' * 40}\n"
        summary += behavior_section[:500] + "...\n"
    
    # Droits essentiels
    rights_section = extract_section(result.content, "DROITS")
    if rights_section:
        summary += f"\n⚖️ VOS DROITS :\n{'-' * 40}\n"
        summary += rights_section[:300] + "...\n"
    
    return summary

def create_print_friendly_summary(result: PreparationClientResult) -> str:
    """Crée une version imprimable de la fiche résumé"""
    
    # Version épurée pour impression A4
    summary = f"""
                    FICHE DE PRÉPARATION
                    {result.prep_type.upper()}
                    
================================================================

CLIENT : _________________________    DATE : {datetime.now().strftime('%d/%m/%Y')}

AVOCAT : _________________________    HEURE : _______________

================================================================

⬜ ATTITUDE GÉNÉRALE :
   - Calme et posé
   - Réponses courtes et précises
   - "Je ne sais pas" si incertain
   - Demander reformulation si nécessaire

⬜ TENUE :
   - Correcte et sobre
   - Éviter signes ostentatoires

================================================================

TOP 5 QUESTIONS CRITIQUES :

1. ____________________________________________________________
   → __________________________________________________________

2. ____________________________________________________________
   → __________________________________________________________

3. ____________________________________________________________
   → __________________________________________________________

4. ____________________________________________________________
   → __________________________________________________________

5. ____________________________________________________________
   → __________________________________________________________

================================================================

⚠️ INTERDICTIONS ABSOLUES :
   ⬜ Pas de spéculation
   ⬜ Pas d'accusation d'autrui
   ⬜ Pas de minimisation excessive
   ⬜ Pas de contradiction
   ⬜ Pas d'aveu même partiel

================================================================

NOTES :
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

================================================================

Signature client : ________________    Signature avocat : ________________
"""
    
    return summary

def highlight_search_terms(content: str, search_term: str) -> str:
    """Surligne les termes recherchés dans le contenu"""
    
    if not search_term:
        return content
    
    # Échapper les caractères spéciaux HTML
    content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Surligner (insensible à la casse)
    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
    highlighted = pattern.sub(
        lambda m: f'<mark style="background-color: yellow;">{m.group()}</mark>',
        content
    )
    
    # Préserver les sauts de ligne
    highlighted = highlighted.replace('\n', '<br>')
    
    return highlighted

def show_interrogation_simulation(result: PreparationClientResult):
    """Mode simulation d'interrogatoire"""
    
    st.markdown("### 🎮 Simulation d'interrogatoire")
    
    # État de la simulation
    if 'simulation_index' not in st.session_state:
        st.session_state.simulation_index = 0
        st.session_state.simulation_score = []
    
    questions = result.key_qa
    current_q = st.session_state.simulation_index
    
    if current_q < len(questions):
        # Question actuelle
        st.info(f"Question {current_q + 1}/{len(questions)}")
        st.subheader(questions[current_q]['question'])
        
        # Zone de réponse
        user_answer = st.text_area(
            "Votre réponse :",
            height=150,
            key=f"sim_answer_{current_q}"
        )
        
        # Afficher la réponse suggérée
        with st.expander("💡 Voir la réponse suggérée"):
            st.success(questions[current_q]['answer'])
            
            # Conseils supplémentaires
            st.info("""
            **Points d'attention :**
            - Restez factuel
            - Évitez les détails inutiles
            - Ne spéculez pas
            - Gardez un ton neutre
            """)
        
        # Évaluation
        st.markdown("#### Auto-évaluation")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Bonne réponse", key=f"good_{current_q}"):
                st.session_state.simulation_score.append(1)
                st.session_state.simulation_index += 1
                st.rerun()
        
        with col2:
            if st.button("😐 Moyenne", key=f"medium_{current_q}"):
                st.session_state.simulation_score.append(0.5)
                st.session_state.simulation_index += 1
                st.rerun()
        
        with col3:
            if st.button("❌ À retravailler", key=f"bad_{current_q}"):
                st.session_state.simulation_score.append(0)
                st.session_state.simulation_index += 1
                st.rerun()
    
    else:
        # Fin de simulation
        display_simulation_results()

def display_simulation_results():
    """Affiche les résultats de la simulation"""
    
    st.success("🎉 Simulation terminée !")
    
    # Calcul du score
    score = st.session_state.simulation_score
    total = sum(score)
    max_score = len(score)
    percentage = (total / max_score * 100) if max_score > 0 else 0
    
    # Affichage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score global", f"{percentage:.0f}%")
    
    with col2:
        st.metric("Questions réussies", f"{score.count(1)}/{len(score)}")
    
    with col3:
        st.metric("À retravailler", score.count(0))
    
    # Graphique de progression
    st.markdown("### 📊 Progression détaillée")
    
    # Créer un graphique simple avec les résultats
    results_display = ""
    for i, s in enumerate(score, 1):
        if s == 1:
            results_display += "🟢"
        elif s == 0.5:
            results_display += "🟡"
        else:
            results_display += "🔴"
        
        if i % 10 == 0:
            results_display += f" {i}\n"
    
    st.text(results_display)
    
    # Recommandations
    st.markdown("### 💡 Recommandations")
    
    if percentage >= 80:
        st.success("""
        Excellente préparation ! Vous maîtrisez bien les réponses.
        - Continuez à réviser les points clés
        - Travaillez la fluidité
        - Restez vigilant sur les questions pièges
        """)
    elif percentage >= 60:
        st.warning("""
        Bonne base, mais des points à améliorer.
        - Revoyez les questions ratées
        - Pratiquez les reformulations
        - Mémorisez les phrases clés
        """)
    else:
        st.error("""
        Préparation insuffisante. Il faut plus de travail.
        - Reprenez la préparation complète
        - Faites plus d'exercices
        - Demandez des sessions supplémentaires
        """)
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Recommencer", key="restart_simulation"):
            st.session_state.simulation_index = 0
            st.session_state.simulation_score = []
            st.rerun()
    
    with col2:
        if st.button("📊 Rapport détaillé", key="detailed_report"):
            report = create_simulation_report(score)
            st.download_button(
                "💾 Télécharger rapport",
                report.encode('utf-8'),
                f"rapport_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain"
            )

def create_simulation_report(scores: List[float]) -> str:
    """Crée un rapport détaillé de la simulation"""
    
    total = sum(scores)
    percentage = (total / len(scores) * 100) if scores else 0
    
    report = f"""RAPPORT DE SIMULATION D'INTERROGATOIRE
{'=' * 50}

Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}
Nombre de questions : {len(scores)}
Score global : {percentage:.1f}%

DÉTAIL PAR QUESTION :
{'-' * 30}
"""
    
    for i, score in enumerate(scores, 1):
        status = "✅ Réussi" if score == 1 else "⚠️ Moyen" if score == 0.5 else "❌ À revoir"
        report += f"Question {i:02d} : {status}\n"
    
    report += f"""
{'-' * 30}
RÉSUMÉ :
- Questions réussies : {scores.count(1)}
- Questions moyennes : {scores.count(0.5)}
- Questions ratées : {scores.count(0)}

RECOMMANDATIONS :
"""
    
    if percentage >= 80:
        report += "- Excellente maîtrise générale\n"
        report += "- Maintenir le niveau par des révisions régulières\n"
    elif percentage >= 60:
        report += "- Niveau satisfaisant mais perfectible\n"
        report += "- Retravailler les questions ratées en priorité\n"
    else:
        report += "- Préparation insuffisante\n"
        report += "- Nécessité de reprendre la formation complète\n"
    
    return report

def show_exercise_timer():
    """Timer pour les exercices de préparation"""
    
    st.markdown("### ⏱️ Chronomètre exercices")
    
    # Exercices prédéfinis avec durées
    exercise_durations = {
        "Présentation personnelle": 60,
        "Récit chronologique": 180,
        "Questions rapides": 120,
        "Gestion du silence": 30,
        "Reformulation": 60,
        "Respiration profonde": 120
    }
    
    selected_exercise = st.selectbox(
        "Choisir l'exercice",
        list(exercise_durations.keys()),
        key="exercise_timer_select"
    )
    
    duration = exercise_durations[selected_exercise]
    
    st.info(f"⏱️ Durée recommandée : {duration} secondes")
    
    # Instructions spécifiques
    instructions = {
        "Présentation personnelle": "Présentez-vous en 1 minute : identité, profession, situation familiale",
        "Récit chronologique": "Racontez les faits de manière chronologique en 3 minutes maximum",
        "Questions rapides": "Répondez à des questions simples le plus rapidement possible",
        "Gestion du silence": "Restez calme et silencieux pendant 30 secondes",
        "Reformulation": "Reformulez des questions complexes en termes simples",
        "Respiration profonde": "Exercice de respiration pour gérer le stress"
    }
    
    st.write(f"**Instructions :** {instructions[selected_exercise]}")
    
    # Timer interface
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Démarrer", key="start_exercise_timer"):
            st.session_state.exercise_start = datetime.now()
            st.session_state.exercise_duration = duration
    
    with col2:
        if 'exercise_start' in st.session_state:
            elapsed = (datetime.now() - st.session_state.exercise_start).seconds
            remaining = max(0, st.session_state.exercise_duration - elapsed)
            
            st.metric("Temps restant", f"{remaining}s")
            
            # Barre de progression
            progress = min(elapsed / st.session_state.exercise_duration, 1.0)
            st.progress(progress)
    
    with col3:
        if st.button("🔄 Réinitialiser", key="reset_exercise_timer"):
            if 'exercise_start' in st.session_state:
                del st.session_state.exercise_start

def show_exercise_practice(exercise: Dict[str, Any]):
    """Interface de pratique pour un exercice"""
    
    st.markdown(f"### 🎯 Pratique : {exercise['title']}")
    
    # Instructions détaillées
    st.info(exercise['description'])
    
    # Zone de pratique selon le type
    if exercise['type'] == 'qa_practice':
        st.text_area(
            "Votre réponse",
            placeholder="Tapez votre réponse ici...",
            height=200,
            key="practice_response"
        )
        
        if st.button("💡 Exemple de bonne réponse"):
            st.success("Réponse type : Je ne me souviens pas précisément de cet événement.")
    
    elif exercise['type'] == 'reformulation':
        st.text_input(
            "Question complexe",
            value="Pouvez-vous expliquer la nature exacte de vos relations avec la société X et justifier les transferts de fonds?",
            disabled=True
        )
        
        reformulation = st.text_area(
            "Votre reformulation",
            placeholder="Reformulez la question...",
            key="reformulation_practice"
        )
        
        if st.button("💡 Exemple"):
            st.success("Reformulation : Vous me demandez quel était mon lien avec la société X et pourquoi il y a eu des virements ?")

def create_mobile_version(result: PreparationClientResult) -> str:
    """Crée une version mobile de la préparation"""
    
    mobile_content = f"""PRÉPARATION MOBILE - {result.prep_type.upper()}
{'=' * 40}

⚡ POINTS ESSENTIELS

📌 ATTITUDE
- Calme et posé
- Réponses courtes
- "Je ne sais pas" si doute
- Demander à reformuler

⚠️ JAMAIS DIRE
"""
    
    # Top 5 des phrases à éviter
    for i, phrase in enumerate(result.do_not_say[:5], 1):
        mobile_content += f"{i}. {phrase}\n"
    
    mobile_content += "\n❓ QUESTIONS CLÉS\n" + "=" * 40 + "\n"
    
    # Top 10 Q/R
    for i, qa in enumerate(result.get_top_questions(10), 1):
        mobile_content += f"\nQ{i}: {qa['question']}\n"
        mobile_content += f"→ {qa['answer']}\n"
        mobile_content += "-" * 40 + "\n"
    
    mobile_content += """
🆘 EN CAS DE DIFFICULTÉ
- Respirer profondément
- Demander à répéter
- "Je dois réfléchir"
- "Je ne comprends pas"

⚖️ VOS DROITS
- Avocat présent
- Refuser de répondre
- Demander une pause
- Accès au dossier
"""
    
    return mobile_content

def export_preparation_to_pdf(result: PreparationClientResult) -> bytes:
    """Exporte la préparation en PDF (version simplifiée)"""
    
    # Version texte formatée
    content = f"""DOCUMENT DE PRÉPARATION
{result.prep_type.upper()}

{'=' * 60}

Généré le : {result.timestamp.strftime('%d/%m/%Y')}
Type : {result.prep_type}
Profil client : {result.profile}
Stratégie : {result.strategy}

{'=' * 60}

{result.content}

{'=' * 60}

Ce document est confidentiel et couvert par le secret professionnel.
"""
    
    return content.encode('utf-8')