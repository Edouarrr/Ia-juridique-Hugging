import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import time
import json

# Configuration de la page
st.set_page_config(
    page_title="IA Juridique Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration des IA disponibles
AVAILABLE_AIS = {
    "GPT-4": {"icon": "🤖", "description": "Analyse approfondie et rédaction complexe"},
    "Claude 3": {"icon": "🧠", "description": "Créativité et argumentation nuancée"},
    "Gemini Pro": {"icon": "✨", "description": "Recherche exhaustive et synthèse"},
    "LLaMA 3": {"icon": "🦙", "description": "Analyse technique et précision"},
    "Mistral": {"icon": "🌟", "description": "Rapidité et concision"}
}

# Fonction CSS améliorée
def load_custom_css():
    st.markdown("""
    <style>
    /* Variables CSS pour les couleurs */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #34495e;
        --accent-color: #3498db;
        --success-color: #27ae60;
        --warning-color: #f39c12;
        --danger-color: #e74c3c;
        --text-primary: #2c3e50;
        --text-secondary: #7f8c8d;
        --border-color: #bdc3c7;
        --hover-color: #ecf0f1;
        --background-light: #f8f9fa;
        --ai-selected: #3498db;
        --ai-hover: #2980b9;
    }
    
    /* Typography */
    h1 { font-size: 1.8rem !important; color: var(--text-primary); margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.5rem !important; color: var(--text-primary); margin-bottom: 0.5rem !important; }
    h3 { font-size: 1.3rem !important; color: var(--text-primary); margin-bottom: 0.5rem !important; }
    h4 { font-size: 1.15rem !important; color: var(--text-primary); margin-bottom: 0.5rem !important; }
    h5 { font-size: 1.05rem !important; color: var(--text-primary); margin-bottom: 0.5rem !important; }
    
    /* Layout optimization */
    .block-container {
        padding-top: 1rem !important;
        max-width: 1400px !important;
    }
    
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* AI Selector Card */
    .ai-selector-card {
        background: white;
        border: 2px solid var(--border-color);
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .ai-selector-card:hover {
        border-color: var(--ai-hover);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .ai-selector-card.selected {
        border-color: var(--ai-selected);
        background: rgba(52, 152, 219, 0.05);
        box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
    }
    
    /* Module Cards */
    .module-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 1px solid var(--border-color);
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .module-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        border-color: var(--accent-color);
    }
    
    .module-icon {
        font-size: 2.5rem;
        margin-bottom: 10px;
    }
    
    .module-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    
    .module-description {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-bottom: 15px;
        flex-grow: 1;
    }
    
    .module-features {
        font-size: 0.8rem;
        color: var(--text-secondary);
        border-top: 1px solid var(--border-color);
        padding-top: 10px;
        margin-top: auto;
    }
    
    /* Search Bar Enhanced */
    .search-container {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        padding: 25px;
        margin: 20px 0;
        border: 1px solid var(--border-color);
    }
    
    .search-container:hover {
        border-color: var(--accent-color);
    }
    
    /* Feature Tags */
    .feature-tag {
        display: inline-block;
        padding: 4px 10px;
        margin: 2px;
        background: var(--hover-color);
        border-radius: 15px;
        font-size: 0.75rem;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--accent-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: var(--ai-hover);
        transform: translateY(-1px);
    }
    
    /* Sidebar enhancement */
    .css-1d391kg {
        background: var(--background-light);
    }
    
    [data-testid="stSidebar"] {
        background: var(--background-light);
    }
    
    /* Response mode selector */
    .response-mode {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Quick action buttons */
    .quick-action {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 10px 15px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
    }
    
    .quick-action:hover {
        border-color: var(--accent-color);
        background: var(--hover-color);
    }
    
    /* AI Response Container */
    .ai-response-container {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .ai-response-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-color);
    }
    
    /* Fusion mode indicator */
    .fusion-indicator {
        background: linear-gradient(45deg, #3498db, #9b59b6);
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Module navigation */
    .module-nav-item {
        padding: 10px 15px;
        margin: 3px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .module-nav-item:hover {
        background: var(--hover-color);
        padding-left: 20px;
    }
    
    .module-nav-item.active {
        background: var(--accent-color);
        color: white;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .module-card {
            margin-bottom: 15px;
        }
        
        .search-container {
            padding: 15px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# État global de l'application
def init_session_state():
    """Initialise les variables de session"""
    if 'selected_ais' not in st.session_state:
        st.session_state.selected_ais = []
    if 'response_mode' not in st.session_state:
        st.session_state.response_mode = 'fusion'
    if 'current_module' not in st.session_state:
        st.session_state.current_module = 'accueil'
    if 'azure_blob_docs' not in st.session_state:
        # Simulation de données Azure Blob
        st.session_state.azure_blob_docs = 1247
        st.session_state.azure_blob_dossiers = 89
    if 'ai_responses' not in st.session_state:
        st.session_state.ai_responses = {}

# Sélecteur d'IA amélioré
def create_ai_selector():
    """Interface de sélection des IA avec fusion des réponses"""
    st.markdown("### 🤖 Sélection des IA")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Sélection multiple des IA
        selected = st.multiselect(
            "Choisissez une ou plusieurs IA",
            options=list(AVAILABLE_AIS.keys()),
            default=st.session_state.selected_ais,
            help="Sélectionnez plusieurs IA pour comparer ou fusionner leurs réponses"
        )
        st.session_state.selected_ais = selected
        
        # Affichage des IA sélectionnées
        if selected:
            cols = st.columns(len(selected))
            for idx, ai in enumerate(selected):
                with cols[idx]:
                    st.markdown(f"""
                    <div class="ai-selector-card selected">
                        <div style="text-align: center;">
                            <div style="font-size: 2rem;">{AVAILABLE_AIS[ai]['icon']}</div>
                            <div style="font-weight: 600; margin: 5px 0;">{ai}</div>
                            <div style="font-size: 0.75rem; color: var(--text-secondary);">
                                {AVAILABLE_AIS[ai]['description']}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        # Mode de réponse
        st.markdown("**Mode de réponse**")
        mode = st.radio(
            "Mode",
            ["fusion", "comparaison", "synthèse"],
            format_func=lambda x: {
                "fusion": "🔄 Fusion complète",
                "comparaison": "📊 Comparaison",
                "synthèse": "📝 Synthèse"
            }[x],
            key="response_mode_selector",
            label_visibility="collapsed"
        )
        st.session_state.response_mode = mode
        
        # Explication du mode
        mode_explanations = {
            "fusion": "Combine toutes les réponses pour maximiser les détails",
            "comparaison": "Affiche les réponses côte à côte",
            "synthèse": "Crée une synthèse concise des points clés"
        }
        st.caption(mode_explanations[mode])

# Barre de navigation latérale améliorée
def create_sidebar():
    """Sidebar avec tous les modules et fonctionnalités"""
    with st.sidebar:
        # Header
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: var(--accent-color); 
                    margin: -35px -35px 20px -35px; border-radius: 0 0 10px 10px;">
            <h2 style="color: white; margin: 0; font-size: 1.3em;">⚖️ IA Juridique Pro</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.8em;">
                Assistant Juridique Intelligent
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Modules principaux
        st.markdown("#### 📚 Modules principaux")
        
        modules = {
            "accueil": {"icon": "🏠", "label": "Accueil & Recherche"},
            "redaction": {"icon": "✍️", "label": "Rédaction IA"},
            "recherche_juridique": {"icon": "⚖️", "label": "Recherche juridique"},
            "analyse": {"icon": "🔍", "label": "Analyse documents"},
            "preparation_client": {"icon": "👔", "label": "Préparation client"},
            "plaidoirie": {"icon": "🎯", "label": "Plaidoirie IA"},
            "conclusions": {"icon": "📋", "label": "Conclusions"},
            "assignation": {"icon": "📜", "label": "Assignations"},
            "contrats": {"icon": "📄", "label": "Contrats"},
            "consultations": {"icon": "💬", "label": "Consultations"},
            "courriers": {"icon": "✉️", "label": "Courriers"},
            "veille": {"icon": "📰", "label": "Veille juridique"}
        }
        
        for key, module in modules.items():
            if st.button(
                f"{module['icon']} {module['label']}", 
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if st.session_state.current_module == key else "secondary"
            ):
                st.session_state.current_module = key
                st.rerun()
        
        st.markdown("---")
        
        # Outils spécialisés
        st.markdown("#### 🛠️ Outils spécialisés")
        
        tools = {
            "timeline": {"icon": "📅", "label": "Timeline affaire"},
            "calculs": {"icon": "🧮", "label": "Calculs juridiques"},
            "modeles": {"icon": "📑", "label": "Modèles documents"},
            "citations": {"icon": "📖", "label": "Gestionnaire citations"},
            "agenda": {"icon": "📆", "label": "Agenda procédures"},
            "tarification": {"icon": "💰", "label": "Calcul honoraires"}
        }
        
        for key, tool in tools.items():
            if st.button(
                f"{tool['icon']} {tool['label']}", 
                key=f"tool_{key}",
                use_container_width=True
            ):
                st.session_state.current_module = key
                st.rerun()
        
        st.markdown("---")
        
        # Gestion & Administration
        st.markdown("#### ⚙️ Gestion")
        
        admin_modules = {
            "documents": {"icon": "📁", "label": "Documents"},
            "clients": {"icon": "👥", "label": "Clients"},
            "dossiers": {"icon": "🗂️", "label": "Dossiers"},
            "facturation": {"icon": "🧾", "label": "Facturation"},
            "statistiques": {"icon": "📊", "label": "Statistiques"},
            "parametres": {"icon": "⚙️", "label": "Paramètres"}
        }
        
        for key, admin in admin_modules.items():
            if st.button(
                f"{admin['icon']} {admin['label']}", 
                key=f"admin_{key}",
                use_container_width=True
            ):
                st.session_state.current_module = key
                st.rerun()
        
        st.markdown("---")
        
        # Statistiques Azure Blob
        st.markdown("#### 📊 Ressources")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", f"{st.session_state.azure_blob_docs:,}", "Azure")
        with col2:
            st.metric("Dossiers", st.session_state.azure_blob_dossiers, "Actifs")

# Page d'accueil avec toutes les fonctionnalités
def show_accueil():
    """Page d'accueil montrant toutes les fonctionnalités"""
    
    # Header compact
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 10px;">⚖️ IA Juridique Pro</h1>
    <p style="text-align: center; color: var(--text-secondary); margin-bottom: 20px;">
        Votre assistant juridique intelligent multi-IA
    </p>
    """, unsafe_allow_html=True)
    
    # Sélecteur d'IA en haut
    create_ai_selector()
    
    st.markdown("---")
    
    # Barre de recherche intelligente
    st.markdown("### 🔍 Recherche intelligente")
    search_query = st.text_area(
        "Posez votre question ou décrivez votre besoin",
        placeholder="Exemples :\n• Comment rédiger des conclusions pour un divorce ?\n• Jurisprudence sur la responsabilité médicale\n• Préparer mon client pour l'audience de demain\n• @Martin (recherche de dossier)",
        height=80,
        key="main_search"
    )
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_type = st.selectbox(
            "Type de recherche",
            ["Tout", "Jurisprudence", "Doctrine", "Dossiers", "Documents", "Modèles"]
        )
    with col2:
        if st.session_state.selected_ais:
            if st.button("🚀 Lancer la recherche IA", type="primary", use_container_width=True):
                if search_query:
                    process_ai_search(search_query, search_type)
        else:
            st.warning("Sélectionnez au moins une IA")
    
    st.markdown("---")
    
    # Grille des fonctionnalités principales
    st.markdown("### 🎯 Fonctionnalités principales")
    
    # Première ligne de fonctionnalités
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">✍️</div>
            <div class="module-title">Rédaction IA</div>
            <div class="module-description">
                Générez tous vos documents juridiques avec l'IA
            </div>
            <div class="module-features">
                <span class="feature-tag">Conclusions</span>
                <span class="feature-tag">Assignations</span>
                <span class="feature-tag">Contrats</span>
                <span class="feature-tag">Courriers</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_redaction", use_container_width=True):
            st.session_state.current_module = "redaction"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">⚖️</div>
            <div class="module-title">Recherche Juridique</div>
            <div class="module-description">
                Accès complet à la jurisprudence et doctrine
            </div>
            <div class="module-features">
                <span class="feature-tag">Cassation</span>
                <span class="feature-tag">CE</span>
                <span class="feature-tag">CA</span>
                <span class="feature-tag">Doctrine</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_recherche", use_container_width=True):
            st.session_state.current_module = "recherche_juridique"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">👔</div>
            <div class="module-title">Préparation Client</div>
            <div class="module-description">
                Préparez efficacement vos clients aux audiences
            </div>
            <div class="module-features">
                <span class="feature-tag">Questions</span>
                <span class="feature-tag">Réponses</span>
                <span class="feature-tag">Stratégie</span>
                <span class="feature-tag">Simulation</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_preparation", use_container_width=True):
            st.session_state.current_module = "preparation_client"
            st.rerun()
    
    with col4:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">🔍</div>
            <div class="module-title">Analyse Documents</div>
            <div class="module-description">
                Analysez et synthétisez vos documents juridiques
            </div>
            <div class="module-features">
                <span class="feature-tag">Risques</span>
                <span class="feature-tag">Points clés</span>
                <span class="feature-tag">Timeline</span>
                <span class="feature-tag">Synthèse</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_analyse", use_container_width=True):
            st.session_state.current_module = "analyse"
            st.rerun()
    
    # Deuxième ligne
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">🎯</div>
            <div class="module-title">Plaidoirie IA</div>
            <div class="module-description">
                Créez des plaidoiries percutantes et structurées
            </div>
            <div class="module-features">
                <span class="feature-tag">Structure</span>
                <span class="feature-tag">Arguments</span>
                <span class="feature-tag">Rhétorique</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_plaidoirie", use_container_width=True):
            st.session_state.current_module = "plaidoirie"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">📰</div>
            <div class="module-title">Veille Juridique</div>
            <div class="module-description">
                Restez informé des dernières actualités juridiques
            </div>
            <div class="module-features">
                <span class="feature-tag">Alertes</span>
                <span class="feature-tag">Actualités</span>
                <span class="feature-tag">Réformes</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_veille", use_container_width=True):
            st.session_state.current_module = "veille"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">🧮</div>
            <div class="module-title">Calculs Juridiques</div>
            <div class="module-description">
                Calculez intérêts, indemnités et prestations
            </div>
            <div class="module-features">
                <span class="feature-tag">Intérêts</span>
                <span class="feature-tag">Art. 700</span>
                <span class="feature-tag">Indemnités</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_calculs", use_container_width=True):
            st.session_state.current_module = "calculs"
            st.rerun()
    
    with col4:
        st.markdown("""
        <div class="module-card">
            <div class="module-icon">📅</div>
            <div class="module-title">Timeline & Agenda</div>
            <div class="module-description">
                Gérez vos délais et échéances procédurales
            </div>
            <div class="module-features">
                <span class="feature-tag">Délais</span>
                <span class="feature-tag">Audiences</span>
                <span class="feature-tag">Rappels</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accéder", key="btn_timeline", use_container_width=True):
            st.session_state.current_module = "timeline"
            st.rerun()
    
    # Actions rapides
    st.markdown("---")
    st.markdown("### ⚡ Actions rapides")
    
    quick_cols = st.columns(6)
    quick_actions = [
        ("📝 Nouvelle conclusion", "conclusions"),
        ("📜 Nouvelle assignation", "assignation"),
        ("📄 Nouveau contrat", "contrats"),
        ("🔍 Analyser document", "analyse"),
        ("👥 Nouveau client", "clients"),
        ("📁 Nouveau dossier", "dossiers")
    ]
    
    for idx, (label, module) in enumerate(quick_actions):
        with quick_cols[idx]:
            if st.button(label, key=f"quick_{module}", use_container_width=True):
                st.session_state.current_module = module
                st.rerun()

# Fonction de traitement des recherches IA
def process_ai_search(query, search_type):
    """Traite les recherches avec les IA sélectionnées"""
    
    if not st.session_state.selected_ais:
        st.warning("Veuillez sélectionner au moins une IA")
        return
    
    # Container pour les réponses
    response_container = st.container()
    
    with response_container:
        st.markdown("### 🤖 Réponses des IA")
        
        # Mode fusion
        if st.session_state.response_mode == "fusion":
            with st.spinner(f"Interrogation de {len(st.session_state.selected_ais)} IA et fusion des réponses..."):
                time.sleep(2)  # Simulation
                
            st.markdown(f"""
            <div class="ai-response-container">
                <div class="ai-response-header">
                    <div class="fusion-indicator">
                        🔄 Réponse fusionnée de {len(st.session_state.selected_ais)} IA
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <h5>Analyse complète sur : "{query}"</h5>
                    <p>Voici la synthèse enrichie combinant les analyses de {', '.join(st.session_state.selected_ais)} :</p>
                    
                    <h6>1. Points juridiques essentiels</h6>
                    <ul>
                        <li><strong>Fondement juridique principal :</strong> Article 1240 du Code civil (responsabilité délictuelle)</li>
                        <li><strong>Jurisprudence consolidée :</strong> Cass. Civ. 2e, 10 mai 2023 établit le principe...</li>
                        <li><strong>Doctrine majoritaire :</strong> Selon Terré et Simler, la notion s'étend...</li>
                    </ul>
                    
                    <h6>2. Argumentation détaillée</h6>
                    <p>L'ensemble des IA convergent sur les arguments suivants, enrichis de leurs perspectives uniques...</p>
                    
                    <h6>3. Stratégie recommandée</h6>
                    <p>Approche en trois temps recommandée par consensus des IA...</p>
                    
                    <h6>4. Points d'attention</h6>
                    <ul>
                        <li>Délai de prescription : attention particulière requise</li>
                        <li>Charge de la preuve : éléments nécessaires identifiés</li>
                        <li>Risques procéduraux : anticipation recommandée</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Mode comparaison
        elif st.session_state.response_mode == "comparaison":
            cols = st.columns(len(st.session_state.selected_ais))
            
            for idx, ai in enumerate(st.session_state.selected_ais):
                with cols[idx]:
                    with st.spinner(f"Interrogation de {ai}..."):
                        time.sleep(1)
                    
                    st.markdown(f"""
                    <div class="ai-response-container">
                        <div style="text-align: center; margin-bottom: 10px;">
                            <span style="font-size: 2rem;">{AVAILABLE_AIS[ai]['icon']}</span>
                            <h5>{ai}</h5>
                        </div>
                        <div style="font-size: 0.9em;">
                            <p><strong>Analyse :</strong> Perspective unique de {ai} sur la question...</p>
                            <p><strong>Points clés :</strong></p>
                            <ul style="font-size: 0.85em;">
                                <li>Point spécifique 1</li>
                                <li>Point spécifique 2</li>
                            </ul>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Mode synthèse
        else:  # synthèse
            with st.spinner("Création de la synthèse concise..."):
                time.sleep(1.5)
            
            st.markdown(f"""
            <div class="ai-response-container">
                <div class="ai-response-header">
                    <div class="fusion-indicator">
                        📝 Synthèse de {len(st.session_state.selected_ais)} IA
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <h5>Synthèse concise</h5>
                    <div style="background: var(--background-light); padding: 15px; border-radius: 8px;">
                        <p><strong>Conclusion principale :</strong> Les {len(st.session_state.selected_ais)} IA s'accordent sur...</p>
                        <p><strong>Actions recommandées :</strong></p>
                        <ol>
                            <li>Action prioritaire 1</li>
                            <li>Action prioritaire 2</li>
                            <li>Action prioritaire 3</li>
                        </ol>
                        <p><strong>Délai suggéré :</strong> 15 jours pour la mise en œuvre</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Module Préparation Client
def show_preparation_client():
    """Module de préparation du client aux audiences"""
    st.title("👔 Préparation du client")
    
    # Sélection IA
    create_ai_selector()
    
    st.markdown("---")
    
    # Informations sur l'affaire
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Nom du client", placeholder="Ex: M. Martin")
        type_audience = st.selectbox(
            "Type d'audience",
            ["Audience de plaidoirie", "Comparution personnelle", "Expertise", "Conciliation", "Référé"]
        )
    
    with col2:
        date_audience = st.date_input("Date de l'audience")
        juridiction = st.text_input("Juridiction", placeholder="Ex: TGI Paris")
    
    # Description de l'affaire
    st.markdown("#### 📋 Contexte de l'affaire")
    contexte = st.text_area(
        "Décrivez l'affaire et les enjeux",
        height=120,
        placeholder="Résumez les faits, les enjeux et les points sensibles..."
    )
    
    # Points à préparer
    st.markdown("#### 🎯 Points spécifiques à préparer")
    col1, col2 = st.columns(2)
    
    with col1:
        points_forts = st.text_area(
            "Points forts du dossier",
            height=100,
            placeholder="Éléments favorables..."
        )
    
    with col2:
        points_faibles = st.text_area(
            "Points à renforcer",
            height=100,
            placeholder="Éléments à expliquer..."
        )
    
    # Options de préparation
    st.markdown("#### ⚙️ Type de préparation")
    preparation_options = st.multiselect(
        "Sélectionnez les éléments à préparer",
        [
            "Questions probables du juge",
            "Réponses types à préparer",
            "Comportement et présentation",
            "Documents à apporter",
            "Stratégie de communication",
            "Simulation d'audience",
            "Points juridiques à expliquer",
            "Gestion du stress"
        ],
        default=["Questions probables du juge", "Réponses types à préparer"]
    )
    
    # Génération
    if st.button("🚀 Générer la préparation", type="primary", use_container_width=True):
        if not st.session_state.selected_ais:
            st.warning("Sélectionnez au moins une IA")
        else:
            with st.spinner("Préparation en cours avec les IA sélectionnées..."):
                time.sleep(2)
            
            st.success("✅ Préparation générée avec succès !")
            
            # Résultats
            st.markdown("### 📋 Guide de préparation")
            
            tabs = st.tabs(["Questions/Réponses", "Comportement", "Documents", "Stratégie", "Simulation"])
            
            with tabs[0]:
                st.markdown("""
                <div class="ai-response-container">
                    <h5>❓ Questions probables et réponses suggérées</h5>
                    
                    <div style="margin: 15px 0; padding: 15px; background: var(--background-light); border-radius: 8px;">
                        <p><strong>Question 1 :</strong> "Pouvez-vous expliquer les circonstances exactes de..."</p>
                        <p><strong>Réponse suggérée :</strong> "Oui, Monsieur/Madame le Président. Le [date], j'ai..."</p>
                        <p style="color: var(--text-secondary); font-size: 0.85em;"><em>💡 Conseil : Restez factuel et chronologique</em></p>
                    </div>
                    
                    <div style="margin: 15px 0; padding: 15px; background: var(--background-light); border-radius: 8px;">
                        <p><strong>Question 2 :</strong> "Qu'avez-vous fait immédiatement après..."</p>
                        <p><strong>Réponse suggérée :</strong> "J'ai immédiatement contacté..."</p>
                        <p style="color: var(--text-secondary); font-size: 0.85em;"><em>💡 Conseil : Montrez votre bonne foi</em></p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with tabs[1]:
                st.markdown("""
                <div class="ai-response-container">
                    <h5>👔 Conseils de comportement et présentation</h5>
                    
                    <h6>Tenue vestimentaire</h6>
                    <ul>
                        <li>Tenue professionnelle sobre (costume/tailleur)</li>
                        <li>Couleurs neutres recommandées</li>
                        <li>Éviter bijoux voyants et parfums forts</li>
                    </ul>
                    
                    <h6>Attitude générale</h6>
                    <ul>
                        <li>Se lever à l'entrée des magistrats</li>
                        <li>S'adresser au juge : "Monsieur/Madame le Président"</li>
                        <li>Parler clairement et distinctement</li>
                        <li>Regarder le juge quand vous répondez</li>
                    </ul>
                    
                    <h6>Gestion du stress</h6>
                    <p>Techniques de respiration recommandées avant l'audience...</p>
                </div>
                """, unsafe_allow_html=True)

# Module Rédaction IA
def show_redaction():
    """Module de rédaction avec IA"""
    st.title("✍️ Rédaction juridique IA")
    
    # Sélection IA
    create_ai_selector()
    
    st.markdown("---")
    
    # Type de document
    doc_type = st.selectbox(
        "Type de document à rédiger",
        [
            "Conclusions",
            "Assignation", 
            "Plaidoirie",
            "Contrat",
            "Consultation juridique",
            "Courrier juridique",
            "Note de synthèse",
            "Requête",
            "Transaction",
            "Mise en demeure"
        ]
    )
    
    # Modèles prédéfinis
    if doc_type == "Conclusions":
        modeles = st.selectbox(
            "Modèle de conclusions",
            ["Vierge", "Divorce", "Responsabilité", "Commercial", "Social", "Pénal"]
        )
    
    # Informations de base
    st.markdown("#### 📋 Informations générales")
    col1, col2 = st.columns(2)
    
    with col1:
        client = st.text_input("Client", placeholder="Nom du client")
        adversaire = st.text_input("Partie adverse", placeholder="Nom de l'adversaire")
    
    with col2:
        juridiction = st.text_input("Juridiction", placeholder="Ex: TGI Paris")
        numero_rg = st.text_input("N° RG", placeholder="Ex: 24/00123")
    
    # Contenu principal
    st.markdown("#### 📝 Contenu")
    
    # Assistant de rédaction
    use_assistant = st.checkbox("🤖 Utiliser l'assistant IA pour structurer")
    
    if use_assistant:
        # Questions guidées selon le type
        if doc_type == "Conclusions":
            faits = st.text_area("Exposé des faits", height=100, 
                               placeholder="Décrivez les faits de manière chronologique...")
            demandes = st.text_area("Demandes du client", height=80,
                                  placeholder="Que demande votre client ?")
            arguments = st.text_area("Arguments juridiques", height=100,
                                   placeholder="Vos moyens et arguments...")
    else:
        # Rédaction libre
        content = st.text_area("Contenu du document", height=300,
                             placeholder="Rédigez ou collez votre texte ici...")
    
    # Options avancées
    with st.expander("⚙️ Options avancées"):
        col1, col2 = st.columns(2)
        with col1:
            tone = st.select_slider(
                "Ton du document",
                options=["Très formel", "Formel", "Neutre", "Direct"],
                value="Formel"
            )
            longueur = st.slider("Longueur cible (pages)", 1, 50, 5)
        
        with col2:
            inclure_jurisprudence = st.checkbox("Inclure jurisprudence pertinente", value=True)
            inclure_doctrine = st.checkbox("Citer la doctrine")
            verifier_delais = st.checkbox("Vérifier les délais procéduraux", value=True)
    
    # Bouton de génération
    if st.button("🚀 Générer avec l'IA", type="primary", use_container_width=True):
        if not st.session_state.selected_ais:
            st.warning("Sélectionnez au moins une IA pour la rédaction")
        else:
            generate_document(doc_type, st.session_state.selected_ais)

def generate_document(doc_type, selected_ais):
    """Génère le document avec les IA sélectionnées"""
    
    with st.spinner(f"Génération en cours avec {len(selected_ais)} IA..."):
        time.sleep(3)
    
    st.success("✅ Document généré avec succès !")
    
    # Affichage selon le mode
    if st.session_state.response_mode == "fusion":
        st.markdown(f"""
        <div class="ai-response-container">
            <div class="ai-response-header">
                <div class="fusion-indicator">
                    🔄 Document fusionné - {len(selected_ais)} IA
                </div>
            </div>
            <div style="margin-top: 20px;">
                <h4>CONCLUSIONS POUR MONSIEUR MARTIN</h4>
                <p style="text-align: center; margin: 20px 0;">
                    <strong>DEVANT LE TRIBUNAL DE GRANDE INSTANCE DE PARIS</strong>
                </p>
                
                <h5>PLAISE AU TRIBUNAL</h5>
                
                <h6>I. FAITS ET PROCÉDURE</h6>
                <p>Les IA ont collaboré pour produire une analyse complète et nuancée des faits...</p>
                
                <h6>II. DISCUSSION</h6>
                <p>A. Sur le fondement juridique</p>
                <p>L'analyse combinée des {len(selected_ais)} IA révèle que...</p>
                
                <h6>III. DEMANDES</h6>
                <p>PAR CES MOTIFS, et tous autres à produire, déduire ou suppléer...</p>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: var(--background-light); border-radius: 8px;">
                <p><strong>📊 Statistiques de génération :</strong></p>
                <ul style="font-size: 0.9em;">
                    <li>Longueur : 2,847 mots</li>
                    <li>Jurisprudences citées : 12</li>
                    <li>Articles de loi : 8</li>
                    <li>Temps de génération : 3.2s</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Actions post-génération
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button("📥 Télécharger Word", data="...", file_name=f"{doc_type}.docx")
    with col2:
        st.download_button("📄 Télécharger PDF", data="...", file_name=f"{doc_type}.pdf")
    with col3:
        if st.button("✏️ Modifier"):
            st.info("Éditeur en cours de chargement...")
    with col4:
        if st.button("📧 Envoyer"):
            st.info("Préparation de l'envoi...")

# Module Recherche Juridique
def show_recherche_juridique():
    """Module de recherche juridique avancée"""
    st.title("⚖️ Recherche juridique intelligente")
    
    # Sélection IA pour analyse
    create_ai_selector()
    
    st.markdown("---")
    
    # Barre de recherche principale
    search_query = st.text_input(
        "🔍 Recherche",
        placeholder="Ex: responsabilité du fait des choses, article 1242, garde juridique...",
        key="juridique_search"
    )
    
    # Filtres avancés
    with st.expander("🔧 Filtres avancés", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sources = st.multiselect(
                "Sources",
                ["Cour de cassation", "Conseil d'État", "Cours d'appel", 
                 "Juridictions du fond", "CJUE", "CEDH", "Doctrine", "Codes"],
                default=["Cour de cassation", "Conseil d'État"]
            )
            
            matieres = st.multiselect(
                "Matières",
                ["Civil", "Pénal", "Commercial", "Social", "Administratif", 
                 "Fiscal", "Famille", "Immobilier", "Propriété intellectuelle"]
            )
        
        with col2:
            date_debut = st.date_input("Date début", value=datetime(2020, 1, 1))
            date_fin = st.date_input("Date fin", value=datetime.now())
            
            importance = st.select_slider(
                "Importance",
                options=["Toutes", "Importantes", "Très importantes", "Principes uniquement"],
                value="Toutes"
            )
        
        with col3:
            recherche_semantique = st.checkbox("Recherche sémantique IA", value=True)
            inclure_doctrine = st.checkbox("Inclure la doctrine", value=True)
            recherche_europeenne = st.checkbox("Inclure droit européen")
            
            tri = st.selectbox(
                "Trier par",
                ["Pertinence", "Date ↓", "Date ↑", "Importance"]
            )
    
    # Recherches suggérées
    st.markdown("#### 💡 Recherches populaires")
    suggested_searches = [
        "Responsabilité médicale 2024",
        "Clause abusive consommateur",
        "Licenciement économique procédure",
        "Garde alternée critères"
    ]
    
    sug_cols = st.columns(len(suggested_searches))
    for idx, suggestion in enumerate(suggested_searches):
        with sug_cols[idx]:
            if st.button(suggestion, key=f"sug_{idx}", use_container_width=True):
                st.session_state.juridique_search = suggestion
                st.rerun()
    
    # Bouton de recherche
    if st.button("🔍 Lancer la recherche", type="primary", use_container_width=True):
        if search_query:
            perform_juridique_search(search_query, sources, st.session_state.selected_ais)

def perform_juridique_search(query, sources, selected_ais):
    """Effectue la recherche juridique avec IA"""
    
    with st.spinner("Recherche en cours dans les bases juridiques..."):
        time.sleep(2)
    
    # Résultats
    st.markdown("### 📚 Résultats de recherche")
    
    # Statistiques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Documents trouvés", "127")
    with col2:
        st.metric("Arrêts de principe", "8")
    with col3:
        st.metric("Articles doctrine", "23")
    with col4:
        st.metric("Score pertinence", "94%")
    
    # Analyse IA si activée
    if selected_ais:
        st.markdown("#### 🤖 Analyse IA des résultats")
        
        if st.session_state.response_mode == "fusion":
            st.markdown(f"""
            <div class="ai-response-container">
                <div class="ai-response-header">
                    <div class="fusion-indicator">
                        🔄 Analyse fusionnée - {len(selected_ais)} IA
                    </div>
                </div>
                <div style="margin-top: 15px;">
                    <h5>Synthèse de la jurisprudence sur "{query}"</h5>
                    
                    <h6>📌 Principe dégagé</h6>
                    <p>La jurisprudence constante établit que {query} implique...</p>
                    
                    <h6>🏛️ Arrêts fondamentaux</h6>
                    <ol>
                        <li><strong>Cass. Civ. 2e, 10 mai 2023, n°22-12.345</strong> : Principe de...</li>
                        <li><strong>CE, 15 mars 2023, n°456789</strong> : Application en matière administrative...</li>
                    </ol>
                    
                    <h6>📈 Évolution jurisprudentielle</h6>
                    <p>On observe une tendance vers...</p>
                    
                    <h6>⚖️ Application pratique</h6>
                    <p>Pour votre dossier, cela signifie que...</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Résultats détaillés
    st.markdown("#### 📋 Documents trouvés")
    
    # Tabs par type
    tabs = st.tabs(["🏛️ Jurisprudence", "📚 Doctrine", "📖 Codes", "🇪🇺 Droit européen"])
    
    with tabs[0]:
        for i in range(3):
            st.markdown(f"""
            <div class="ai-response-container" style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex-grow: 1;">
                        <h5 style="margin: 0; color: var(--accent-color);">
                            Cass. Civ. 2e, {10-i} janvier 2024, n°23-{12345+i}
                        </h5>
                        <p style="margin: 5px 0; font-size: 0.85em; color: var(--text-secondary);">
                            <strong>Mots-clés :</strong> Responsabilité • Préjudice • Réparation intégrale
                        </p>
                        <p style="margin: 10px 0; font-size: 0.9em;">
                            "Attendu que la responsabilité du fait des choses suppose la réunion de trois conditions : 
                            une chose, instrument du dommage, sous la garde de celui dont la responsabilité est recherchée..."
                        </p>
                        <div style="margin-top: 10px;">
                            <span class="feature-tag">⭐ Arrêt de principe</span>
                            <span class="feature-tag">Revirement</span>
                        </div>
                    </div>
                    <div style="margin-left: 20px;">
                        <button style="padding: 5px 10px; margin: 2px;">📄 Texte intégral</button><br>
                        <button style="padding: 5px 10px; margin: 2px;">💾 Sauvegarder</button><br>
                        <button style="padding: 5px 10px; margin: 2px;">📋 Citer</button>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Fonction principale
def main():
    """Point d'entrée principal de l'application"""
    
    # Initialisation
    init_session_state()
    load_custom_css()
    
    # Sidebar
    create_sidebar()
    
    # Routeur vers les modules
    module_functions = {
        "accueil": show_accueil,
        "redaction": show_redaction,
        "recherche_juridique": show_recherche_juridique,
        "preparation_client": show_preparation_client,
        "analyse": lambda: st.info("Module Analyse en développement..."),
        "plaidoirie": lambda: st.info("Module Plaidoirie en développement..."),
        "conclusions": lambda: st.info("Module Conclusions en développement..."),
        "assignation": lambda: st.info("Module Assignations en développement..."),
        "contrats": lambda: st.info("Module Contrats en développement..."),
        "consultations": lambda: st.info("Module Consultations en développement..."),
        "courriers": lambda: st.info("Module Courriers en développement..."),
        "veille": lambda: st.info("Module Veille juridique en développement..."),
        "timeline": lambda: st.info("Module Timeline en développement..."),
        "calculs": lambda: st.info("Module Calculs juridiques en développement..."),
        "modeles": lambda: st.info("Module Modèles en développement..."),
        "citations": lambda: st.info("Module Citations en développement..."),
        "agenda": lambda: st.info("Module Agenda en développement..."),
        "tarification": lambda: st.info("Module Tarification en développement..."),
        "documents": lambda: st.info("Module Documents en développement..."),
        "clients": lambda: st.info("Module Clients en développement..."),
        "dossiers": lambda: st.info("Module Dossiers en développement..."),
        "facturation": lambda: st.info("Module Facturation en développement..."),
        "statistiques": lambda: st.info("Module Statistiques en développement..."),
        "parametres": lambda: st.info("Module Paramètres en développement...")
    }
    
    # Affichage du module sélectionné
    current_module = st.session_state.current_module
    if current_module in module_functions:
        module_functions[current_module]()
    else:
        show_accueil()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<p style='text-align: center; color: #7f8c8d; font-size: 0.8em;'>
        ⚖️ IA Juridique Pro • Assistant multi-IA pour professionnels du droit
        </p>""",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()