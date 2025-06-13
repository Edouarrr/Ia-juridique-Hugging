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
    "GPT-3.5": {"icon": "🤖", "description": "Analyse rapide des pièces procédurales"},
    "GPT-4": {"icon": "🧠", "description": "Analyse approfondie et contradictions dans les pièces"},
    "Azure OpenAI": {"icon": "☁️", "description": "IA sécurisée pour pièces confidentielles"},
    "Claude Opus 4": {"icon": "🎭", "description": "Argumentation basée sur les pièces du dossier"},
    "Gemini": {"icon": "✨", "description": "Recherche exhaustive dans toutes les pièces"},
    "Mistral": {"icon": "🌟", "description": "Analyse juridique des pièces françaises"}
}

# Base de données enrichie avec les pièces du dossier
DOSSIERS_CLIENTS = {
    "lesueur": {
        "info": {
            "nom": "M. Lesueur",
            "affaire": "ABS SAS TechFinance", 
            "qualification": "Abus de biens sociaux - Art. 314-1",
            "statut": "Mis en examen",
            "audience": "15/02/2024 - Tribunal correctionnel",
            "montant": "450 000 €"
        },
        "pieces": {
            "PV": [
                {"ref": "PV-001", "titre": "PV audition garde à vue Lesueur", "date": "10/01/2024", "pages": 45},
                {"ref": "PV-002", "titre": "PV perquisition siège social", "date": "08/01/2024", "pages": 23},
                {"ref": "PV-003", "titre": "PV audition comptable société", "date": "12/01/2024", "pages": 18}
            ],
            "Expertises": [
                {"ref": "EXP-001", "titre": "Rapport expertise comptable", "date": "20/01/2024", "pages": 156},
                {"ref": "EXP-002", "titre": "Analyse flux financiers 2022-2023", "date": "22/01/2024", "pages": 89}
            ],
            "Documents_saisis": [
                {"ref": "SCEL-001", "titre": "Relevés bancaires SAS TechFinance", "periode": "2022-2023", "pages": 234},
                {"ref": "SCEL-002", "titre": "Factures litigieuses", "nombre": 47, "pages": 94},
                {"ref": "SCEL-003", "titre": "Contrats prestations fictives", "nombre": 12, "pages": 156},
                {"ref": "SCEL-004", "titre": "Emails direction", "nombre": 1247, "pages": 890}
            ],
            "Procedures": [
                {"ref": "PROC-001", "titre": "Ordonnance de mise en examen", "date": "15/01/2024", "pages": 8},
                {"ref": "PROC-002", "titre": "Réquisitoire supplétif", "date": "25/01/2024", "pages": 12}
            ]
        }
    },
    "martin": {
        "info": {
            "nom": "Mme Martin",
            "affaire": "Blanchiment réseau crypto",
            "qualification": "Blanchiment aggravé - Art. 324-1",
            "statut": "Témoin assisté", 
            "audience": "20/02/2024 - Juge d'instruction",
            "montant": "2.3 M€"
        },
        "pieces": {
            "PV": [
                {"ref": "PV-101", "titre": "PV audition libre Martin", "date": "05/01/2024", "pages": 28},
                {"ref": "PV-102", "titre": "PV exploitation données blockchain", "date": "15/01/2024", "pages": 167}
            ],
            "Expertises": [
                {"ref": "EXP-101", "titre": "Rapport TRACFIN", "date": "01/12/2023", "pages": 43},
                {"ref": "EXP-102", "titre": "Expertise crypto-actifs", "date": "18/01/2024", "pages": 78}
            ],
            "Documents_saisis": [
                {"ref": "SCEL-101", "titre": "Wallets crypto identifiés", "nombre": 23, "pages": 145},
                {"ref": "SCEL-102", "titre": "Virements SEPA suspects", "nombre": 156, "pages": 312}
            ],
            "Procedures": [
                {"ref": "PROC-101", "titre": "Convocation témoin assisté", "date": "10/01/2024", "pages": 3}
            ]
        }
    },
    "dupont": {
        "info": {
            "nom": "M. Dupont", 
            "affaire": "Corruption marché public BTP",
            "qualification": "Corruption active agent public",
            "statut": "Mis en examen",
            "audience": "25/02/2024 - Chambre de l'instruction",
            "montant": "1.8 M€"
        },
        "pieces": {
            "PV": [
                {"ref": "PV-201", "titre": "PV interpellation Dupont", "date": "03/01/2024", "pages": 15},
                {"ref": "PV-202", "titre": "PV écoutes téléphoniques", "date": "Déc 2023", "pages": 456}
            ],
            "Expertises": [
                {"ref": "EXP-201", "titre": "Analyse marchés publics truqués", "date": "20/01/2024", "pages": 234}
            ],
            "Documents_saisis": [
                {"ref": "SCEL-201", "titre": "Cahiers des charges modifiés", "nombre": 8, "pages": 89},
                {"ref": "SCEL-202", "titre": "Versements occultes", "nombre": 34, "pages": 67}
            ],
            "Procedures": [
                {"ref": "PROC-201", "titre": "Commission rogatoire internationale", "date": "15/01/2024", "pages": 23}
            ]
        }
    }
}

# Suggestions de prompts basées sur les pièces
def generate_piece_based_prompts(client_key, pieces):
    """Génère des prompts basés sur les pièces du dossier"""
    prompts = []
    
    # Prompts basés sur les PV
    if pieces.get("PV"):
        for pv in pieces["PV"][:2]:
            prompts.append(f"Analyser contradictions dans {pv['titre']} (Ref: {pv['ref']})")
            prompts.append(f"Identifier points faibles {pv['ref']} pages clés")
    
    # Prompts basés sur les expertises
    if pieces.get("Expertises"):
        for exp in pieces["Expertises"][:2]:
            prompts.append(f"Contester conclusions {exp['titre']} (Ref: {exp['ref']})")
            prompts.append(f"Extraire éléments favorables {exp['ref']}")
    
    # Prompts basés sur les documents saisis
    if pieces.get("Documents_saisis"):
        for doc in pieces["Documents_saisis"][:2]:
            prompts.append(f"Analyser {doc['titre']} pour éléments à décharge")
            prompts.append(f"Vérifier authenticité pièces {doc['ref']}")
    
    # Prompts croisés
    if pieces.get("PV") and pieces.get("Expertises"):
        prompts.append(f"Comparer {pieces['PV'][0]['ref']} avec {pieces['Expertises'][0]['ref']} - incohérences")
    
    return prompts

# Questions basées sur les pièces pour la préparation
def generate_piece_based_questions(module_theme, pieces, client_info):
    """Génère des questions basées sur les pièces spécifiques du dossier"""
    questions = []
    
    if "faits" in module_theme.lower() or "intentionnel" in module_theme.lower():
        if pieces.get("PV"):
            pv = pieces["PV"][0]
            questions.extend([
                f"❓ Dans votre audition du {pv['date']} ({pv['ref']} p.12-15), vous déclarez ne pas connaître ces virements. Comment l'expliquez-vous ?",
                f"❓ Le {pv['ref']} mentionne votre signature sur 23 ordres de virement. Vous souvenez-vous de ces documents ?",
                f"❓ Page 34 du {pv['ref']}, vous reconnaissez avoir rencontré M. X. Dans quel contexte ?"
            ])
        
        if pieces.get("Documents_saisis"):
            doc = pieces["Documents_saisis"][0]
            questions.extend([
                f"❓ Les {doc['titre']} ({doc['ref']}) montrent {doc.get('nombre', 'plusieurs')} opérations suspectes. Quelle était leur finalité ?",
                f"❓ Comment justifiez-vous l'absence de contrepartie dans les pièces {doc['ref']} ?"
            ])
    
    elif "financ" in module_theme.lower() or "flux" in module_theme.lower():
        if pieces.get("Expertises"):
            exp = pieces["Expertises"][0]
            questions.extend([
                f"❓ Le {exp['titre']} ({exp['ref']} p.45-67) identifie {client_info['montant']} de flux suspects. D'où provenaient ces fonds ?",
                f"❓ L'expert relève page 89 du {exp['ref']} des virements vers des paradis fiscaux. Quelle en était la raison ?",
                f"❓ Comment expliquez-vous les conclusions de l'expertise {exp['ref']} sur les surfacturations ?"
            ])
    
    elif "société" in module_theme.lower() or "organisation" in module_theme.lower():
        if pieces.get("Documents_saisis"):
            for doc in pieces["Documents_saisis"]:
                if "email" in doc['titre'].lower():
                    questions.append(f"❓ Les {doc['nombre']} emails saisis ({doc['ref']}) montrent que vous étiez informé. Qu'en dites-vous ?")
                if "contrat" in doc['titre'].lower():
                    questions.append(f"❓ Les {doc.get('nombre', '')} contrats ({doc['ref']}) étaient-ils tous réels ?")
    
    # Questions sur les contradictions entre pièces
    if len(pieces.get("PV", [])) > 1:
        questions.append(f"❓ Vos déclarations dans {pieces['PV'][0]['ref']} contredisent celles du {pieces['PV'][1]['ref']}. Comment l'expliquez-vous ?")
    
    return questions

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
        --piece-bg: #fff3cd;
    }
    
    /* Pièces du dossier */
    .piece-card {
        background: var(--piece-bg);
        border: 1px solid #ffc107;
        border-radius: 6px;
        padding: 10px;
        margin: 5px 0;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .piece-card:hover {
        background: #ffe69c;
        transform: translateX(3px);
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
    }
    
    .piece-ref {
        font-weight: 700;
        color: var(--danger-color);
        margin-right: 8px;
    }
    
    .piece-pages {
        float: right;
        color: var(--text-secondary);
        font-size: 0.8rem;
    }
    
    /* Container pièces */
    .pieces-container {
        background: white;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .pieces-category {
        font-weight: 600;
        color: var(--accent-color);
        margin: 10px 0 5px 0;
        font-size: 0.9rem;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 3px;
    }
    
    /* Prompts basés sur pièces */
    .piece-prompt {
        background: white;
        border: 1px solid var(--border-color);
        border-left: 3px solid #ffc107;
        border-radius: 4px;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
    }
    
    .piece-prompt:hover {
        background: var(--piece-bg);
        transform: translateX(5px);
    }
    
    .piece-prompt .piece-ref {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: #ffc107;
        color: #000;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    /* Questions avec références */
    .question-with-piece {
        background: var(--background-light);
        border-left: 4px solid var(--accent-color);
        padding: 12px;
        margin: 8px 0;
        position: relative;
    }
    
    .question-with-piece .piece-citation {
        font-weight: 600;
        color: #d35400;
        text-decoration: underline;
    }
    
    /* Client mode avec pièces */
    .search-container.client-mode {
        border-color: #ffc107;
        background: linear-gradient(to right, #fff3cd 0%, white 100%);
    }
    
    /* Stats pièces */
    .pieces-stats {
        display: flex;
        gap: 10px;
        margin: 10px 0;
    }
    
    .piece-stat {
        background: var(--piece-bg);
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid #ffc107;
    }
    
    /* Layout ultra-compact */
    .block-container {
        padding-top: 0.5rem !important;
        max-width: 1600px !important;
    }
    
    /* Typography compacte */
    h1 { font-size: 1.4rem !important; margin-bottom: 0.3rem !important; }
    h2 { font-size: 1.2rem !important; margin-bottom: 0.3rem !important; }
    h3 { font-size: 1.05rem !important; margin-bottom: 0.3rem !important; }
    h4 { font-size: 0.95rem !important; margin-bottom: 0.3rem !important; }
    h5 { font-size: 0.85rem !important; margin-bottom: 0.3rem !important; }
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
    if 'current_client' not in st.session_state:
        st.session_state.current_client = None
    if 'selected_pieces' not in st.session_state:
        st.session_state.selected_pieces = []

# Affichage des pièces du dossier
def display_dossier_pieces(client_key):
    """Affiche les pièces disponibles dans le dossier"""
    if client_key not in DOSSIERS_CLIENTS:
        return
    
    pieces = DOSSIERS_CLIENTS[client_key]["pieces"]
    client_info = DOSSIERS_CLIENTS[client_key]["info"]
    
    # Stats des pièces
    total_pieces = sum(len(pieces[cat]) for cat in pieces)
    total_pages = sum(p.get('pages', 0) for cat in pieces for p in pieces[cat])
    
    st.markdown(f"""
    <div class="pieces-stats">
        <span class="piece-stat">📁 {total_pieces} pièces</span>
        <span class="piece-stat">📄 {total_pages} pages</span>
        <span class="piece-stat">💰 {client_info['montant']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Container des pièces
    st.markdown('<div class="pieces-container">', unsafe_allow_html=True)
    
    # Affichage par catégorie
    for category, items in pieces.items():
        if items:
            st.markdown(f'<div class="pieces-category">📂 {category.replace("_", " ").title()}</div>', unsafe_allow_html=True)
            
            for piece in items:
                piece_id = f"{client_key}_{piece['ref']}"
                selected = piece_id in st.session_state.selected_pieces
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""
                    <div class="piece-card">
                        <span class="piece-ref">{piece['ref']}</span>
                        {piece['titre']}
                        <span class="piece-pages">{piece.get('pages', 'N/A')} pages</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.checkbox("", key=f"select_{piece_id}", value=selected):
                        if piece_id not in st.session_state.selected_pieces:
                            st.session_state.selected_pieces.append(piece_id)
                    else:
                        if piece_id in st.session_state.selected_pieces:
                            st.session_state.selected_pieces.remove(piece_id)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Barre de recherche avec contexte pièces
def create_smart_search_with_pieces():
    """Barre de recherche intégrant les pièces du dossier"""
    
    # JavaScript pour détection @client
    search_js = """
    <script>
    function setupPieceAwareSearch() {
        const checkTextarea = setInterval(function() {
            const textarea = document.querySelector('textarea[aria-label="main_search_pieces"]');
            if (textarea) {
                clearInterval(checkTextarea);
                
                let debounceTimer;
                
                textarea.addEventListener('input', function(event) {
                    clearTimeout(debounceTimer);
                    const value = textarea.value;
                    
                    if (value.startsWith('@')) {
                        textarea.style.borderColor = '#ffc107';
                        textarea.style.backgroundColor = '#fff3cd';
                        textarea.style.borderWidth = '2px';
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
    
    setupPieceAwareSearch();
    const observer = new MutationObserver(setupPieceAwareSearch);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    # Détection du client
    query = st.session_state.get('search_query', '')
    client_detected = False
    client_key = None
    
    if query.startswith("@"):
        parts = query[1:].split(",", 1)
        potential_client = parts[0].strip().lower()
        if potential_client in DOSSIERS_CLIENTS:
            client_detected = True
            client_key = potential_client
            st.session_state.current_client = client_key
    
    # Container avec style adaptatif
    container_class = "search-container client-mode" if client_detected else "search-container"
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    # Affichage selon le mode
    if client_detected:
        client_info = DOSSIERS_CLIENTS[client_key]["info"]
        st.markdown(f"### 📁 Dossier {client_info['nom']} - {client_info['affaire']}")
        
        # Affichage des pièces
        with st.expander("📂 Pièces du dossier", expanded=True):
            display_dossier_pieces(client_key)
    else:
        st.markdown("### 🔍 Recherche intelligente avec analyse des pièces")
    
    # Zone de recherche
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_area(
            "main_search_pieces",
            placeholder=(
                "Exemples avec pièces :\n"
                "• @Lesueur, analyser contradictions PV-001 vs EXP-001\n"
                "• @Martin, préparer défense sur SCEL-101 (wallets crypto)\n"
                "• @Dupont, contester écoutes PV-202"
            ),
            height=80,
            key="search_query",
            label_visibility="hidden"
        )
    
    with col2:
        st.write("")
        if st.button("🤖 Analyser", type="primary", use_container_width=True):
            if query:
                st.session_state.current_view = "analyze_with_pieces"
                st.rerun()
    
    # Suggestions basées sur les pièces
    if client_detected and client_key:
        pieces = DOSSIERS_CLIENTS[client_key]["pieces"]
        
        st.markdown("#### 💡 Analyses suggérées basées sur les pièces")
        
        # Générer des prompts basés sur les pièces
        piece_prompts = generate_piece_based_prompts(client_key, pieces)
        
        for prompt in piece_prompts[:5]:
            if st.button(f"→ {prompt}", key=f"pp_{prompt[:30]}", use_container_width=True):
                st.session_state.search_query = f"@{client_key}, {prompt}"
                st.rerun()
        
        # Actions rapides sur pièces sélectionnées
        if st.session_state.selected_pieces:
            st.markdown("#### ⚡ Actions sur pièces sélectionnées")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Analyser contradictions", use_container_width=True):
                    st.session_state.search_query = f"@{client_key}, analyser contradictions dans {', '.join(st.session_state.selected_pieces)}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()
            with col2:
                if st.button("📋 Synthétiser", use_container_width=True):
                    st.session_state.search_query = f"@{client_key}, synthétiser {', '.join(st.session_state.selected_pieces)}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()
            with col3:
                if st.button("⚖️ Stratégie défense", use_container_width=True):
                    st.session_state.search_query = f"@{client_key}, stratégie défense basée sur {', '.join(st.session_state.selected_pieces)}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Injecter JavaScript
    components.html(search_js, height=0)
    
    return query

# Module de préparation avec pièces
def show_preparation_with_pieces():
    """Préparation client basée sur les pièces du dossier"""
    if not st.session_state.current_client:
        st.warning("Aucun client sélectionné")
        return
    
    client_key = st.session_state.current_client
    client = DOSSIERS_CLIENTS[client_key]["info"]
    pieces = DOSSIERS_CLIENTS[client_key]["pieces"]
    
    st.markdown(f"## 👔 Préparation de {client['nom']} - Basée sur les pièces")
    
    # Rappel du dossier
    st.markdown(f"""
    <div class="preparation-card">
        <strong>📁 Affaire :</strong> {client['affaire']}<br>
        <strong>⚖️ Qualification :</strong> {client['qualification']}<br>
        <strong>📅 Audience :</strong> {client['audience']}<br>
        <strong>💰 Enjeu :</strong> {client['montant']}
    </div>
    """, unsafe_allow_html=True)
    
    # Sélection IA
    create_ai_selector_mini()
    
    st.markdown("---")
    
    # Modules de préparation
    modules = {
        "questions_pieces": "Questions sur les pièces du dossier",
        "contradictions": "Contradictions entre pièces", 
        "elements_defense": "Éléments favorables dans les pièces",
        "strategie_pieces": "Stratégie basée sur les pièces"
    }
    
    for module_key, module_title in modules.items():
        with st.expander(f"📋 {module_title}", expanded=module_key=="questions_pieces"):
            
            if st.button(f"🤖 Générer avec IA", key=f"gen_{module_key}"):
                if not st.session_state.selected_ais:
                    st.warning("Sélectionnez au moins une IA")
                else:
                    with st.spinner(f"Analyse des pièces par {len(st.session_state.selected_ais)} IA..."):
                        time.sleep(1.5)
                    
                    if module_key == "questions_pieces":
                        # Questions basées sur les vraies pièces
                        questions = generate_piece_based_questions("questions sur pièces", pieces, client)
                        
                        for q in questions[:6]:
                            st.markdown(f"""
                            <div class="question-with-piece">
                                {q}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Conseils spécifiques
                        st.success("""
                        💡 **Conseils pour répondre sur les pièces :**
                        • Relisez les passages cités avant l'audience
                        • Préparez des explications cohérentes avec l'ensemble du dossier
                        • N'hésitez pas à demander à consulter la pièce pendant l'audience
                        • Restez cohérent avec vos déclarations antérieures (PV-001)
                        """)
                    
                    elif module_key == "contradictions":
                        st.markdown("""
                        <div class="ai-response-container">
                            <h4>⚠️ Contradictions identifiées</h4>
                            <ul>
                                <li><strong>PV-001 vs EXP-001 :</strong> Vos déclarations sur les dates contredisent l'expertise</li>
                                <li><strong>SCEL-002 vs SCEL-003 :</strong> Les factures ne correspondent pas aux contrats</li>
                                <li><strong>PV-001 p.23 vs PV-003 p.45 :</strong> Versions différentes sur les signatures</li>
                            </ul>
                            <p><strong>Stratégie :</strong> Préparer des explications cohérentes pour chaque contradiction</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    elif module_key == "elements_defense":
                        st.markdown(f"""
                        <div class="ai-response-container">
                            <h4>✅ Éléments favorables identifiés</h4>
                            <ul>
                                <li><strong>EXP-001 p.89 :</strong> L'expert reconnaît l'absence de dissimulation</li>
                                <li><strong>SCEL-004 :</strong> Emails montrant votre bonne foi</li>
                                <li><strong>PV-003 :</strong> Le comptable confirme votre version sur 3 points</li>
                            </ul>
                            <p><strong>À exploiter :</strong> Insister sur ces éléments pendant l'audience</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Notes sur les pièces
            notes = st.text_area(
                f"Notes sur les pièces ({module_key})",
                key=f"notes_{module_key}",
                placeholder="Points clés des pièces à retenir...",
                height=80
            )
    
    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Générer mémo pièces", type="primary", use_container_width=True):
            st.success("Mémo des pièces clés généré")
    
    with col2:
        if st.button("🎯 Simulation avec pièces", use_container_width=True):
            st.info("Simulation basée sur les pièces...")
    
    with col3:
        if st.button("⬅️ Retour", use_container_width=True):
            st.session_state.current_view = 'dashboard'
            st.rerun()

# Analyse avec pièces
def analyze_query_with_pieces():
    """Analyse une requête en se basant sur les pièces du dossier"""
    query = st.session_state.search_query
    
    if not st.session_state.selected_ais:
        st.warning("Sélectionnez au moins une IA")
        return
    
    # Extraire le client et la commande
    client_key = st.session_state.current_client
    if not client_key and query.startswith("@"):
        parts = query[1:].split(",", 1)
        potential_client = parts[0].strip().lower()
        if potential_client in DOSSIERS_CLIENTS:
            client_key = potential_client
    
    if not client_key:
        st.error("Client non identifié")
        return
    
    client = DOSSIERS_CLIENTS[client_key]["info"]
    pieces = DOSSIERS_CLIENTS[client_key]["pieces"]
    
    st.markdown(f"### 🤖 Analyse pour {client['nom']}")
    st.markdown(f"**Requête :** {query}")
    st.markdown(f"**IA actives :** {', '.join(st.session_state.selected_ais)}")
    
    with st.spinner(f"Analyse des pièces du dossier par {len(st.session_state.selected_ais)} IA..."):
        time.sleep(2)
    
    # Réponse basée sur les pièces
    if st.session_state.response_mode == "fusion":
        st.markdown(f"""
        <div class="ai-response-container">
            <h4>🔄 Analyse fusionnée multi-IA basée sur les pièces</h4>
            
            <h5>📁 Pièces analysées :</h5>
            <ul>
                <li>PV-001 : PV audition garde à vue (45 pages)</li>
                <li>EXP-001 : Rapport expertise comptable (156 pages)</li>
                <li>SCEL-002 : Factures litigieuses (94 pages)</li>
            </ul>
            
            <h5>🔍 Analyse détaillée :</h5>
            
            <h6>1. Sur les contradictions identifiées (GPT-4 + Claude Opus 4)</h6>
            <p>L'analyse croisée du <span class="piece-citation">PV-001 pages 12-15</span> avec le 
            <span class="piece-citation">rapport d'expertise EXP-001 pages 45-67</span> révèle 3 contradictions majeures...</p>
            
            <h6>2. Sur l'élément intentionnel (Azure OpenAI + Mistral)</h6>
            <p>Les <span class="piece-citation">emails SCEL-004</span> démontrent l'absence d'intention frauduleuse. 
            Notamment l'email du 15/03/2023 où vous alertez sur les irrégularités...</p>
            
            <h6>3. Sur la prescription (Gemini + GPT-3.5)</h6>
            <p>Selon les <span class="piece-citation">relevés bancaires SCEL-001</span>, les premiers faits 
            remontent à plus de 6 ans (prescription acquise pour 45% des montants)...</p>
            
            <h5>⚖️ Stratégie recommandée :</h5>
            <ol>
                <li>Exploiter les contradictions entre PV-001 et EXP-001</li>
                <li>S'appuyer sur SCEL-004 pour démontrer la bonne foi</li>
                <li>Invoquer la prescription partielle basée sur SCEL-001</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Actions post-analyse
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📑 Tableau contradictions", use_container_width=True):
            st.info("Génération tableau...")
    
    with col2:
        if st.button("📊 Graphique timeline", use_container_width=True):
            st.info("Création timeline...")
    
    with col3:
        if st.button("✍️ Rédiger conclusions", use_container_width=True):
            st.session_state.current_view = "redaction"
            st.rerun()
    
    with col4:
        if st.button("⬅️ Nouvelle analyse", use_container_width=True):
            st.session_state.current_view = "dashboard"
            st.rerun()

# Sélecteur IA compact
def create_ai_selector_mini():
    """Sélecteur d'IA compact"""
    st.markdown("#### 🤖 Sélection des IA")
    
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
    
    # Mode
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

# Sidebar avec pièces
def create_sidebar():
    """Sidebar avec accès rapide aux dossiers"""
    with st.sidebar:
        # Header
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #1a1a2e, #e94560); 
                    margin: -35px -35px 15px -35px; border-radius: 0 0 10px 10px;">
            <h3 style="color: white; margin: 0; font-size: 1.1rem;">⚖️ IA Pénal - Pièces</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # IA actives
        if st.session_state.selected_ais:
            st.markdown("#### 🤖 IA actives")
            ia_list = " • ".join([AVAILABLE_AIS[ai]['icon'] for ai in st.session_state.selected_ais])
            st.markdown(f"<div style='text-align: center; font-size: 1.2rem;'>{ia_list}</div>", unsafe_allow_html=True)
        
        # Dossiers clients avec stats pièces
        st.markdown("---")
        st.markdown("#### 📁 Dossiers actifs")
        
        for client_key, client_data in DOSSIERS_CLIENTS.items():
            client = client_data["info"]
            pieces = client_data["pieces"]
            total_pieces = sum(len(pieces[cat]) for cat in pieces)
            
            if st.button(
                f"→ {client['nom']} ({total_pieces} pièces)",
                key=f"sidebar_{client_key}",
                use_container_width=True,
                type="primary" if st.session_state.current_client == client_key else "secondary"
            ):
                st.session_state.search_query = f"@{client_key}, analyser dossier"
                st.session_state.current_client = client_key
                st.session_state.current_view = "dashboard"
                st.rerun()
        
        # Navigation
        st.markdown("---")
        st.markdown("#### 📊 Modules")
        
        modules = [
            ("🏠 Accueil", "dashboard"),
            ("👔 Préparation", "preparation"),
            ("🔍 Analyse pièces", "analyze_pieces"),
            ("✍️ Rédaction", "redaction"),
            ("📊 Statistiques", "stats")
        ]
        
        for label, view in modules:
            if st.button(label, key=f"nav_{view}", use_container_width=True):
                st.session_state.current_view = view
                st.rerun()
        
        # Alertes pièces manquantes
        st.markdown("---")
        st.markdown("#### ⚠️ Alertes")
        st.warning("📄 PV confrontation manquant (Lesueur)", icon="⚠️")
        st.error("⏰ Délai communication pièces : 5j", icon="🚨")

# Dashboard principal
def show_dashboard():
    """Dashboard avec focus sur les pièces"""
    
    # Header
    st.markdown("""
    <h1 style="text-align: center; margin: 5px 0;">⚖️ IA Juridique - Analyse des Pièces</h1>
    <p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem;">
        Analyse intelligente basée sur les pièces du dossier • 6 IA spécialisées
    </p>
    """, unsafe_allow_html=True)
    
    # Sélecteur IA
    create_ai_selector_mini()
    
    st.markdown("---")
    
    # Barre de recherche avec pièces
    query = create_smart_search_with_pieces()
    
    # Stats globales des pièces
    if not st.session_state.current_client:
        st.markdown("### 📊 Vue d'ensemble des dossiers")
        
        cols = st.columns(len(DOSSIERS_CLIENTS))
        for idx, (client_key, client_data) in enumerate(DOSSIERS_CLIENTS.items()):
            with cols[idx]:
                client = client_data["info"]
                pieces = client_data["pieces"]
                total_pieces = sum(len(pieces[cat]) for cat in pieces)
                total_pages = sum(p.get('pages', 0) for cat in pieces for p in pieces[cat])
                
                st.markdown(f"""
                <div class="module-card">
                    <h4>{client['nom']}</h4>
                    <p style="font-size: 0.8rem; margin: 5px 0;">{client['affaire']}</p>
                    <div class="pieces-stats" style="justify-content: center;">
                        <span class="piece-stat" style="font-size: 0.7rem;">📁 {total_pieces}</span>
                        <span class="piece-stat" style="font-size: 0.7rem;">📄 {total_pages}p</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Analyser", key=f"analyze_{client_key}", use_container_width=True):
                    st.session_state.search_query = f"@{client_key}, vue d'ensemble"
                    st.session_state.current_client = client_key
                    st.rerun()
    
    # Actions rapides basées sur les pièces
    if st.session_state.current_client:
        st.markdown("### ⚡ Actions rapides sur les pièces")
        
        quick_cols = st.columns(5)
        actions = [
            ("🔍 Contradictions", "identifier contradictions entre pièces"),
            ("📊 Timeline", "créer timeline avec pièces"),
            ("✅ Éléments favorables", "extraire éléments favorables"),
            ("⚠️ Points faibles", "identifier risques dans pièces"),
            ("📑 Synthèse", "synthétiser toutes les pièces")
        ]
        
        for idx, (label, action) in enumerate(actions):
            with quick_cols[idx]:
                if st.button(label, key=f"quick_{action[:10]}", use_container_width=True):
                    st.session_state.search_query = f"@{st.session_state.current_client}, {action}"
                    st.session_state.current_view = "analyze_with_pieces"
                    st.rerun()

# Router principal
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
        "preparation": show_preparation_with_pieces,
        "analyze_with_pieces": analyze_query_with_pieces,
        "analyze_pieces": lambda: st.info("🔍 Module d'analyse approfondie des pièces en développement"),
        "redaction": lambda: st.info("✍️ Module de rédaction basée sur les pièces en développement"),
        "stats": lambda: st.info("📊 Module de statistiques des pièces en développement")
    }
    
    # Affichage
    current_view = st.session_state.current_view
    if current_view in views:
        views[current_view]()
    else:
        show_dashboard()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: #95a5a6; font-size: 0.7rem;'>
        ⚖️ IA Juridique Pénal • Analyse basée sur les pièces • RGPD
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()