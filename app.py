import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import time
import json

# Configuration de la page
st.set_page_config(
    page_title="IA Juridique - Droit Pénal des Affaires",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration des IA disponibles
AVAILABLE_AIS = {
    "GPT-3.5": {"icon": "🤖", "description": "Analyse rapide et réponses structurées"},
    "GPT-4": {"icon": "🧠", "description": "Analyse approfondie et raisonnement complexe"},
    "Azure OpenAI": {"icon": "☁️", "description": "IA sécurisée pour données sensibles"},
    "Claude Opus 4": {"icon": "🎭", "description": "Argumentation nuancée et créative"},
    "Gemini": {"icon": "✨", "description": "Recherche exhaustive multimodale"},
    "Mistral": {"icon": "🌟", "description": "Spécialiste droit français et européen"}
}

# Base de clients pour la préparation
CLIENTS_DB = {
    "lesueur": {
        "nom": "M. Lesueur",
        "affaire": "ABS SAS TechFinance",
        "qualification": "Abus de biens sociaux",
        "statut": "Mis en examen",
        "audience": "15/02/2024 - Tribunal correctionnel"
    },
    "martin": {
        "nom": "Mme Martin",
        "affaire": "Blanchiment réseau international",
        "qualification": "Blanchiment aggravé",
        "statut": "Témoin assisté",
        "audience": "20/02/2024 - Juge d'instruction"
    },
    "dupont": {
        "nom": "M. Dupont",
        "affaire": "Corruption marché public",
        "qualification": "Corruption active",
        "statut": "Mis en examen",
        "audience": "25/02/2024 - Chambre de l'instruction"
    }
}

# Modules de préparation client
PREPARATION_MODULES = {
    "questions_tribunal": {
        "titre": "Questions du tribunal",
        "themes": [
            "Questions sur les faits",
            "Questions sur l'organisation de la société",
            "Questions sur votre rôle et responsabilités",
            "Questions sur les flux financiers",
            "Questions sur votre connaissance des faits"
        ]
    },
    "questions_procureur": {
        "titre": "Questions du procureur",
        "themes": [
            "Questions pièges sur l'intentionnalité",
            "Questions sur les contradictions",
            "Questions sur les documents",
            "Questions sur les témoignages",
            "Questions sur les antécédents"
        ]
    },
    "comportement": {
        "titre": "Comportement à l'audience",
        "themes": [
            "Attitude générale et présentation",
            "Gestion du stress et des émotions",
            "Communication non-verbale",
            "Formules de politesse",
            "Réactions aux provocations"
        ]
    },
    "strategie": {
        "titre": "Stratégie de défense",
        "themes": [
            "Points forts à mettre en avant",
            "Points faibles à minimiser",
            "Éléments de contexte favorables",
            "Arguments juridiques clés",
            "Ligne de défense cohérente"
        ]
    }
}

# Suggestions de prompts enrichies avec modules
PROMPT_SUGGESTIONS = {
    "prépar": [
        "préparer client audience correctionnelle",
        "préparer interrogatoire juge instruction",
        "préparer questions procureur ABS",
        "préparer confrontation témoins",
        "préparer plaidoirie partie civile"
    ],
    "rédac": [
        "rédiger conclusions ABS défense",
        "rédiger plainte constitution partie civile",
        "rédiger mémoire cassation pénal",
        "rédiger observations expertise comptable",
        "rédiger requête nullité procédure"
    ],
    "analys": [
        "analyser PV audition garde à vue",
        "analyser rapport expertise financière",
        "analyser scellés documents comptables",
        "analyser contradictions témoignages",
        "analyser risques mise en examen"
    ],
    "recherch": [
        "rechercher jurisprudence ABS prescription",
        "rechercher jurisprudence blanchiment auto-blanchiment",
        "rechercher arrêts corruption élément moral",
        "rechercher doctrine nullités procédure",
        "rechercher CEDH délai raisonnable"
    ],
    "calcul": [
        "calculer délai appel correctionnel",
        "calculer prescription ABS dissimulé",
        "calculer intérêts civils préjudice",
        "calculer honoraires complexité dossier",
        "calculer délai cassation pénal"
    ]
}

# Fonction CSS optimisée
def load_custom_css():
    st.markdown("""
    <style>
    /* Variables CSS adaptées au pénal des affaires */
    :root {
        --primary-color: #1a1a2e;
        --secondary-color: #16213e;
        --accent-color: #e94560;
        --success-color: #0f3460;
        --warning-color: #f39c12;
        --danger-color: #c0392b;
        --text-primary: #2c3e50;
        --text-secondary: #7f8c8d;
        --border-color: #bdc3c7;
        --hover-color: #ecf0f1;
        --background-light: #f8f9fa;
        --ai-selected: #e94560;
        --ai-hover: #c0392b;
        --penal-bg: #fef5f5;
        --client-bg: #e8f5e9;
    }
    
    /* Typography ultra-compacte */
    h1 { font-size: 1.5rem !important; margin-bottom: 0.3rem !important; }
    h2 { font-size: 1.25rem !important; margin-bottom: 0.3rem !important; }
    h3 { font-size: 1.1rem !important; margin-bottom: 0.3rem !important; }
    h4 { font-size: 1rem !important; margin-bottom: 0.3rem !important; }
    h5 { font-size: 0.9rem !important; margin-bottom: 0.3rem !important; }
    
    /* Layout ultra-compact */
    .block-container {
        padding-top: 0.5rem !important;
        max-width: 1600px !important;
    }
    
    /* Préparation client card */
    .preparation-card {
        background: var(--client-bg);
        border: 2px solid #4caf50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .preparation-theme {
        background: white;
        border: 1px solid #4caf50;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .preparation-theme:hover {
        background: #f1f8e9;
        transform: translateX(5px);
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
    }
    
    .client-info-badge {
        background: #4caf50;
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    }
    
    /* Suggestion de prompts améliorée */
    .prompt-suggestion {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 8px 12px;
        margin: 3px 0;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s ease;
        position: relative;
    }
    
    .prompt-suggestion:hover {
        background: var(--penal-bg);
        border-color: var(--accent-color);
        transform: translateX(5px);
    }
    
    .prompt-module-tag {
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        background: var(--accent-color);
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
    }
    
    /* AI Selector optimisé */
    .ai-selector-mini {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px;
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        margin: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .ai-selector-mini:hover {
        border-color: var(--ai-hover);
        background: var(--hover-color);
    }
    
    .ai-selector-mini.selected {
        border-color: var(--ai-selected);
        background: var(--penal-bg);
        font-weight: 600;
    }
    
    /* Module Cards ultra-compactes */
    .module-card {
        background: white;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 1px solid var(--border-color);
        height: 100%;
        min-height: 120px;
    }
    
    .module-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        border-color: var(--accent-color);
    }
    
    /* Search container avec détection client */
    .search-container {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        padding: 20px;
        margin: 15px 0;
        border: 1px solid var(--border-color);
        position: relative;
    }
    
    .search-container.client-mode {
        border-color: #4caf50;
        background: #f1f8e9;
    }
    
    /* Questions preview */
    .question-preview {
        background: var(--background-light);
        border-left: 3px solid var(--accent-color);
        padding: 10px;
        margin: 5px 0;
        font-size: 0.85rem;
    }
    
    .question-category {
        font-weight: 600;
        color: var(--accent-color);
        margin-bottom: 5px;
    }
    
    /* Responsive optimisé */
    @media (max-width: 768px) {
        .module-card {
            min-height: 100px;
            padding: 10px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# État global
def init_session_state():
    """Initialise les variables de session"""
    if 'selected_ais' not in st.session_state:
        st.session_state.selected_ais = []
    if 'response_mode' not in st.session_state:
        st.session_state.response_mode = 'fusion'
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'dashboard'
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'client_mode' not in st.session_state:
        st.session_state.client_mode = None
    if 'preparation_themes' not in st.session_state:
        st.session_state.preparation_themes = []

# Fonction pour détecter et traiter les commandes client
def process_client_command(query):
    """Détecte et traite les commandes @client"""
    if query.startswith("@"):
        parts = query[1:].split(",", 1)
        client_name = parts[0].strip().lower()
        
        if client_name in CLIENTS_DB:
            client = CLIENTS_DB[client_name]
            command = parts[1].strip() if len(parts) > 1 else ""
            
            return {
                "is_client_command": True,
                "client": client,
                "client_key": client_name,
                "command": command
            }
    
    return {"is_client_command": False}

# Générateur de prompts intelligent avec modules
def get_smart_suggestions(query, client_context=None):
    """Génère des suggestions basées sur les modules et le contexte"""
    suggestions = {}
    query_lower = query.lower()
    
    # Si contexte client, prioriser la préparation
    if client_context:
        suggestions["préparation_audience"] = [
            f"Préparer {client_context['nom']} - Questions sur {client_context['qualification']}",
            f"Simuler interrogatoire {client_context['statut']} - {client_context['affaire']}",
            f"Stratégie défense {client_context['audience']}",
            f"Points faibles à travailler avec {client_context['nom']}",
            f"Documents à préparer pour {client_context['nom']}"
        ]
    
    # Suggestions basées sur les mots-clés
    for keyword, prompts in PROMPT_SUGGESTIONS.items():
        if keyword in query_lower:
            # Ajouter le module associé
            module_map = {
                "prépar": "👔 Préparation",
                "rédac": "✍️ Rédaction",
                "analys": "🔍 Analyse",
                "recherch": "⚖️ Recherche",
                "calcul": "🧮 Calculs"
            }
            module = module_map.get(keyword, "")
            suggestions[keyword] = [(p, module) for p in prompts[:4]]
    
    # Suggestions contextuelles si pas de match
    if not suggestions and len(query) > 3:
        suggestions["suggestions_modules"] = [
            (f"✍️ Rédiger {query}", "✍️ Rédaction"),
            (f"🔍 Analyser {query}", "🔍 Analyse"),
            (f"⚖️ Rechercher jurisprudence {query}", "⚖️ Recherche"),
            (f"👔 Préparer client pour {query}", "👔 Préparation")
        ]
    
    return suggestions

# Barre de recherche intelligente avec détection client
def create_smart_search_bar():
    """Barre de recherche avec IA et détection @client"""
    
    # JavaScript amélioré
    search_js = """
    <script>
    function setupEnhancedSearch() {
        const checkTextarea = setInterval(function() {
            const textarea = document.querySelector('textarea[aria-label="main_search"]');
            if (textarea) {
                clearInterval(checkTextarea);
                
                let debounceTimer;
                
                textarea.addEventListener('input', function(event) {
                    clearTimeout(debounceTimer);
                    const value = textarea.value;
                    
                    // Style différent pour @client
                    if (value.startsWith('@')) {
                        textarea.style.borderColor = '#4caf50';
                        textarea.style.backgroundColor = '#f1f8e9';
                        
                        // Extraire le nom du client
                        const clientPart = value.substring(1).split(',')[0];
                        if (clientPart.length > 2) {
                            textarea.style.borderWidth = '2px';
                        }
                    } else {
                        textarea.style.borderColor = '';
                        textarea.style.backgroundColor = '';
                        textarea.style.borderWidth = '';
                    }
                    
                    debounceTimer = setTimeout(() => {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        nativeInputValueSetter.call(textarea, value);
                        const inputEvent = new Event('input', { bubbles: true });
                        textarea.dispatchEvent(inputEvent);
                    }, 300);
                });
                
                textarea.addEventListener('keydown', function(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        const buttons = document.querySelectorAll('button');
                        buttons.forEach(button => {
                            if (button.textContent.includes('Analyser')) {
                                button.click();
                            }
                        });
                    }
                });
                
                textarea.focus();
            }
        }, 100);
    }
    
    setupEnhancedSearch();
    const observer = new MutationObserver(setupEnhancedSearch);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    # Container principal
    client_context = process_client_command(st.session_state.get('search_query', ''))
    container_class = "search-container client-mode" if client_context['is_client_command'] else "search-container"
    
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    # Titre adaptatif
    if client_context['is_client_command']:
        st.markdown(f"### 👔 Préparation de {client_context['client']['nom']}")
        st.markdown(f"""
        <div>
            <span class="client-info-badge">📁 {client_context['client']['affaire']}</span>
            <span class="client-info-badge">⚖️ {client_context['client']['qualification']}</span>
            <span class="client-info-badge">📅 {client_context['client']['audience']}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🔍 Recherche intelligente IA - Droit Pénal des Affaires")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_area(
            "main_search",
            placeholder=(
                "Exemples :\n"
                "• @Lesueur, préparer pour l'audience\n"
                "• @Martin, questions du procureur sur blanchiment\n"
                "• Analyser PV garde à vue\n"
                "• Rédiger conclusions ABS"
            ),
            height=80,
            key="search_query",
            label_visibility="hidden"
        )
    
    with col2:
        st.write("")  # Alignement
        if st.button("🤖 Analyser", type="primary", use_container_width=True):
            if query:
                st.session_state.current_view = "process_query"
                st.rerun()
    
    # Traitement des suggestions
    if query:
        client_cmd = process_client_command(query)
        
        if client_cmd['is_client_command']:
            # Mode préparation client
            st.markdown("#### 📋 Modules de préparation disponibles")
            
            for module_key, module_info in PREPARATION_MODULES.items():
                st.markdown(f"""
                <div class="preparation-theme">
                    <h5>{module_info['titre']}</h5>
                    <div style="font-size: 0.85rem; color: var(--text-secondary);">
                        {len(module_info['themes'])} thèmes • Durée estimée : {len(module_info['themes']) * 30} min
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Préparer {module_info['titre']}", key=f"prep_{module_key}", use_container_width=True):
                    st.session_state.preparation_module = module_key
                    st.session_state.current_client = client_cmd['client_key']
                    st.session_state.current_view = "preparation_detail"
                    st.rerun()
            
            # Suggestions de séances thématiques
            st.markdown("#### 🎯 Séances thématiques suggérées")
            themes = [
                "📌 Questions sur l'élément intentionnel (crucial en ABS)",
                "📌 Chronologie des faits et cohérence du récit",
                "📌 Documents comptables et justificatifs",
                "📌 Relations avec les co-mis en examen",
                "📌 Stratégie face aux parties civiles"
            ]
            for theme in themes[:3]:
                st.info(theme)
        
        else:
            # Mode recherche normale avec suggestions
            suggestions = get_smart_suggestions(query)
            
            if suggestions:
                st.markdown("#### 💡 Suggestions IA basées sur les modules")
                
                for category, items in suggestions.items():
                    for item in items:
                        if isinstance(item, tuple):
                            prompt, module = item
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                if st.button(f"→ {prompt}", key=f"sug_{prompt[:30]}", use_container_width=True):
                                    st.session_state.search_query = prompt
                                    st.rerun()
                            with col2:
                                st.markdown(f'<span class="prompt-module-tag">{module}</span>', unsafe_allow_html=True)
                        else:
                            if st.button(f"→ {item}", key=f"sug_{item[:30]}", use_container_width=True):
                                st.session_state.search_query = item
                                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Injecter JavaScript
    components.html(search_js, height=0)
    
    return query

# Sélecteur d'IA compact optimisé
def create_ai_selector_mini():
    """Sélecteur d'IA version ultra-compacte"""
    st.markdown("### 🤖 IA disponibles")
    
    # Affichage en grille 2x3
    cols = st.columns(3)
    for idx, (ai_name, ai_info) in enumerate(AVAILABLE_AIS.items()):
        with cols[idx % 3]:
            selected = ai_name in st.session_state.selected_ais
            
            if st.checkbox(
                f"{ai_info['icon']} {ai_name}",
                value=selected,
                key=f"ai_{ai_name}",
                help=ai_info['description']
            ):
                if ai_name not in st.session_state.selected_ais:
                    st.session_state.selected_ais.append(ai_name)
            else:
                if ai_name in st.session_state.selected_ais:
                    st.session_state.selected_ais.remove(ai_name)
    
    # Mode de fusion
    if st.session_state.selected_ais:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Fusion", key="mode_fusion", use_container_width=True,
                        type="primary" if st.session_state.response_mode == "fusion" else "secondary"):
                st.session_state.response_mode = "fusion"
        with col2:
            if st.button("📊 Comparaison", key="mode_comp", use_container_width=True,
                        type="primary" if st.session_state.response_mode == "comparaison" else "secondary"):
                st.session_state.response_mode = "comparaison"
        with col3:
            if st.button("📝 Synthèse", key="mode_synth", use_container_width=True,
                        type="primary" if st.session_state.response_mode == "synthèse" else "secondary"):
                st.session_state.response_mode = "synthèse"

# Page de préparation détaillée
def show_preparation_detail():
    """Affiche le détail de préparation client avec questions"""
    if 'preparation_module' not in st.session_state:
        st.session_state.current_view = 'dashboard'
        st.rerun()
        return
    
    module = PREPARATION_MODULES[st.session_state.preparation_module]
    client = CLIENTS_DB[st.session_state.current_client]
    
    # Header
    st.markdown(f"""
    <h2>👔 Préparation de {client['nom']}</h2>
    <h3>{module['titre']}</h3>
    """, unsafe_allow_html=True)
    
    # Info client
    st.markdown(f"""
    <div class="preparation-card">
        <strong>Affaire :</strong> {client['affaire']}<br>
        <strong>Qualification :</strong> {client['qualification']}<br>
        <strong>Audience :</strong> {client['audience']}
    </div>
    """, unsafe_allow_html=True)
    
    # Sélection IA pour génération
    create_ai_selector_mini()
    
    st.markdown("---")
    
    # Thèmes et questions
    st.markdown("### 📋 Séances thématiques")
    
    for idx, theme in enumerate(module['themes']):
        with st.expander(f"**Séance {idx+1} : {theme}**", expanded=idx==0):
            
            # Générer des questions avec IA
            if st.button(f"🤖 Générer questions IA", key=f"gen_{idx}"):
                if not st.session_state.selected_ais:
                    st.warning("Sélectionnez au moins une IA")
                else:
                    with st.spinner(f"Génération par {len(st.session_state.selected_ais)} IA..."):
                        time.sleep(1.5)
                    
                    # Questions générées selon le thème
                    if "intentionnel" in theme.lower() or "faits" in theme.lower():
                        questions = [
                            "❓ Pouvez-vous m'expliquer précisément votre rôle dans la société au moment des faits ?",
                            "❓ Aviez-vous connaissance du caractère irrégulier de ces opérations ?",
                            "❓ Qui a donné l'ordre de procéder à ces virements ?",
                            "❓ Quel bénéfice personnel en avez-vous retiré ?",
                            "❓ Comment expliquez-vous ces mouvements de fonds ?"
                        ]
                    elif "organisation" in theme.lower() or "société" in theme.lower():
                        questions = [
                            "❓ Décrivez l'organigramme de la société",
                            "❓ Qui avait le pouvoir de signature sur les comptes ?",
                            "❓ Comment étaient prises les décisions importantes ?",
                            "❓ Y avait-il des procédures de contrôle interne ?",
                            "❓ Qui validait les dépenses exceptionnelles ?"
                        ]
                    elif "flux" in theme.lower() or "financ" in theme.lower():
                        questions = [
                            "❓ Expliquez la destination de ces fonds",
                            "❓ Pourquoi ces virements vers des comptes personnels ?",
                            "❓ Comment justifiez-vous ces montants ?",
                            "❓ Y avait-il des contreparties à ces paiements ?",
                            "❓ Qui bénéficiait in fine de ces sommes ?"
                        ]
                    else:
                        questions = [
                            "❓ Question générale adaptée au thème",
                            "❓ Question de suivi pour approfondir",
                            "❓ Question piège potentielle",
                            "❓ Question de cohérence avec les pièces",
                            "❓ Question finale de synthèse"
                        ]
                    
                    # Affichage des questions
                    for q in questions:
                        st.markdown(f"""
                        <div class="question-preview">
                            <div class="question-category">{'Tribunal' if idx % 2 == 0 else 'Procureur'}</div>
                            {q}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Conseils de réponse
                    st.markdown("#### 💡 Conseils pour répondre")
                    st.success("""
                    • Restez factuel et chronologique
                    • Ne spéculez pas sur les intentions d'autrui
                    • Référez-vous aux documents quand possible
                    • Admettez ne pas savoir plutôt que d'inventer
                    • Gardez votre calme face aux questions agressives
                    """)
            
            # Zone de notes
            notes = st.text_area(
                "Notes de préparation",
                key=f"notes_{idx}",
                placeholder="Points clés à retenir, réponses à préparer...",
                height=100
            )
            
            # Durée estimée
            st.info(f"⏱️ Durée estimée : 30-45 minutes")
    
    # Actions finales
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Générer fiche complète", type="primary", use_container_width=True):
            st.success("Fiche de préparation générée")
    
    with col2:
        if st.button("🎯 Simulation d'audience", use_container_width=True):
            st.info("Module simulation en développement")
    
    with col3:
        if st.button("📧 Envoyer au client", use_container_width=True):
            st.info("Envoi par email...")
    
    with col4:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.current_view = 'dashboard'
            st.rerun()

# Sidebar optimisée
def create_sidebar():
    """Sidebar avec navigation et stats"""
    with st.sidebar:
        # Header
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #1a1a2e, #e94560); 
                    margin: -35px -35px 15px -35px; border-radius: 0 0 10px 10px;">
            <h3 style="color: white; margin: 0; font-size: 1.1rem;">⚖️ IA Pénal des Affaires</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # IA sélectionnées
        if st.session_state.selected_ais:
            st.markdown("#### 🤖 IA actives")
            ia_list = " • ".join([AVAILABLE_AIS[ai]['icon'] for ai in st.session_state.selected_ais])
            st.markdown(f"<div style='text-align: center; font-size: 1.2rem;'>{ia_list}</div>", unsafe_allow_html=True)
            st.markdown("---")
        
        # Navigation principale
        st.markdown("#### 📊 Modules")
        
        modules = [
            ("🏠 Tableau de bord", "dashboard"),
            ("👔 Préparation client", "preparation"),
            ("✍️ Rédaction pénale", "redaction"),
            ("⚖️ Recherche juridique", "recherche"),
            ("🔍 Analyse dossiers", "analyse"),
            ("⏱️ Suivi temps", "temps"),
            ("📁 Documents", "documents"),
            ("📊 Statistiques", "stats")
        ]
        
        for label, key in modules:
            if st.button(label, key=f"nav_{key}", use_container_width=True,
                        type="primary" if st.session_state.current_view == key else "secondary"):
                st.session_state.current_view = key
                st.rerun()
        
        # Stats rapides
        st.markdown("---")
        st.markdown("#### 🚨 Urgences")
        st.error("⏰ Délai appel : 3j", icon="🚨")
        st.warning("📅 Audience demain", icon="⚠️")
        
        # Clients en préparation
        st.markdown("---")
        st.markdown("#### 👥 Clients actifs")
        for client_key, client in list(CLIENTS_DB.items())[:3]:
            if st.button(f"→ {client['nom']}", key=f"quick_client_{client_key}", use_container_width=True):
                st.session_state.search_query = f"@{client_key}, préparer audience"
                st.session_state.current_view = "dashboard"
                st.rerun()

# Page Tableau de bord principal
def show_dashboard():
    """Dashboard avec toutes les fonctionnalités"""
    
    # Header minimal
    st.markdown("""
    <h1 style="text-align: center; margin: 5px 0;">⚖️ IA Juridique - Droit Pénal des Affaires</h1>
    <p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 10px;">
        6 IA spécialisées • Préparation client intelligente • Modules interconnectés
    </p>
    """, unsafe_allow_html=True)
    
    # Sélecteur IA
    create_ai_selector_mini()
    
    st.markdown("---")
    
    # Barre de recherche intelligente
    query = create_smart_search_bar()
    
    # Si une requête est en cours de traitement
    if st.session_state.current_view == "process_query" and query:
        process_main_query(query)
        return
    
    # Modules principaux en grille compacte
    st.markdown("### 🎯 Modules spécialisés")
    
    # Ligne 1 : Modules métier
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    module_configs = [
        ("👔", "Préparation Client", "Questions tribunal • Simulation • Comportement", "preparation"),
        ("✍️", "Rédaction IA", "Conclusions • Plaintes • Mémoires", "redaction"),
        ("⚖️", "Recherche", "Jurisprudence • Doctrine • CEDH", "recherche"),
        ("🔍", "Analyse", "PV • Expertises • Stratégie", "analyse"),
        ("⏱️", "Temps", "Timer • Facturation • Stats", "temps"),
        ("📊", "Stats", "Taux succès • Délais • KPI", "stats")
    ]
    
    for idx, (icon, title, desc, view) in enumerate(module_configs):
        with [col1, col2, col3, col4, col5, col6][idx]:
            st.markdown(f"""
            <div class="module-card">
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">{icon}</div>
                    <div style="font-weight: 600; font-size: 0.85rem; margin: 5px 0;">{title}</div>
                    <div style="font-size: 0.7rem; color: var(--text-secondary);">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Ouvrir", key=f"btn_{view}", use_container_width=True):
                st.session_state.current_view = view
                st.rerun()
    
    # Ligne 2 : Infractions
    st.markdown("### 🚨 Infractions pénales")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    infractions = [
        ("💰", "ABS", "Abus biens sociaux"),
        ("🔄", "Blanchiment", "TRACFIN • Aggravé"),
        ("🎭", "Corruption", "Active • Passive"),
        ("📈", "Boursier", "Initié • AMF"),
        ("🔗", "Escroquerie", "Faux • Crypto"),
        ("🏦", "Banqueroute", "Frauduleuse")
    ]
    
    for idx, (icon, title, desc) in enumerate(infractions):
        with [col1, col2, col3, col4, col5, col6][idx]:
            st.markdown(f"""
            <div class="module-card" style="min-height: 90px;">
                <div style="text-align: center;">
                    <div style="font-size: 1.5rem;">{icon}</div>
                    <div style="font-weight: 600; font-size: 0.8rem;">{title}</div>
                    <div style="font-size: 0.65rem; color: var(--text-secondary);">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Actions rapides
    st.markdown("### ⚡ Actions rapides")
    
    quick_cols = st.columns(10)
    quick_actions = [
        ("🚨", "Plainte"),
        ("📄", "Constit. PC"),
        ("⏰", "Délais"),
        ("💰", "Honoraires"),
        ("📊", "Rapport"),
        ("🔍", "Analyse PV"),
        ("📅", "Audience"),
        ("💳", "TRACFIN"),
        ("📝", "Nullité"),
        ("⚖️", "QPC")
    ]
    
    for idx, (icon, label) in enumerate(quick_actions):
        with quick_cols[idx]:
            if st.button(f"{icon}\n{label}", key=f"quick_{label}", use_container_width=True):
                st.info(f"Module {label} en développement")

# Traitement des requêtes principales
def process_main_query(query):
    """Traite les requêtes avec IA"""
    
    # Vérifier si c'est une commande client
    client_cmd = process_client_command(query)
    
    if client_cmd['is_client_command']:
        # Rediriger vers la préparation
        st.session_state.current_view = 'preparation_detail'
        st.session_state.current_client = client_cmd['client_key']
        st.session_state.preparation_module = 'questions_tribunal'
        st.rerun()
    else:
        # Traitement normal avec IA
        if not st.session_state.selected_ais:
            st.warning("⚠️ Sélectionnez au moins une IA pour analyser votre requête")
            if st.button("⬅️ Retour"):
                st.session_state.current_view = 'dashboard'
                st.rerun()
            return
        
        st.markdown(f"### 🤖 Analyse : *{query}*")
        st.markdown(f"**IA actives :** {', '.join(st.session_state.selected_ais)}")
        st.markdown(f"**Mode :** {st.session_state.response_mode}")
        
        with st.spinner(f"Interrogation de {len(st.session_state.selected_ais)} IA..."):
            time.sleep(2)
        
        # Résultats selon le mode
        if st.session_state.response_mode == "fusion":
            st.markdown("""
            <div class="ai-response-container">
                <h4>🔄 Réponse fusionnée multi-IA</h4>
                <p>Analyse croisée pour une réponse complète et nuancée...</p>
                <ul>
                    <li>Point 1 enrichi par GPT-4 et Claude Opus 4</li>
                    <li>Point 2 complété par Azure OpenAI</li>
                    <li>Point 3 vérifié par Gemini et Mistral</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("⬅️ Nouvelle recherche", type="primary"):
            st.session_state.current_view = 'dashboard'
            st.rerun()

# Fonction principale
def main():
    """Point d'entrée principal"""
    
    # Initialisation
    init_session_state()
    load_custom_css()
    
    # Sidebar
    create_sidebar()
    
    # Router
    views = {
        "dashboard": show_dashboard,
        "preparation": lambda: st.info("👔 Module Préparation client - Utilisez @NomClient dans la recherche"),
        "preparation_detail": show_preparation_detail,
        "process_query": lambda: process_main_query(st.session_state.search_query),
        "redaction": lambda: st.info("✍️ Module Rédaction en développement"),
        "recherche": lambda: st.info("⚖️ Module Recherche en développement"),
        "analyse": lambda: st.info("🔍 Module Analyse en développement"),
        "temps": lambda: st.info("⏱️ Module Temps en développement"),
        "documents": lambda: st.info("📁 Module Documents en développement"),
        "stats": lambda: st.info("📊 Module Statistiques en développement")
    }
    
    # Affichage
    current_view = st.session_state.current_view
    if current_view in views:
        views[current_view]()
    else:
        show_dashboard()
    
    # Footer minimal
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: #95a5a6; font-size: 0.7rem;'>
        ⚖️ IA Juridique Pénal des Affaires | 6 IA | RGPD
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()