import streamlit as st
import os
import sys
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import time
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Nexora Law IA - Assistant Juridique",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation minimale de l'état de session
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.active_module = None
    st.session_state.search_performed = False
    st.session_state.documents_count = {'local': 0, 'containers': {}}
    st.session_state.selected_modules = []
    st.session_state.search_mode = 'global'
    st.session_state.ai_model = 'claude-opus-4'
    st.session_state.search_history = []
    st.session_state.active_container = None

# CSS professionnel avec dégradés de bleu
st.markdown("""
<style>
    /* Variables de couleurs */
    :root {
        --primary-blue: #1e3a8a;
        --secondary-blue: #3b82f6;
        --light-blue: #dbeafe;
        --bg-blue: #f0f9ff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
    }
    
    /* Styles généraux */
    .main { padding: 0 !important; }
    .block-container { padding: 2rem 1rem !important; max-width: 1400px !important; }
    
    /* Barre latérale stylisée */
    .css-1d391kg { background-color: var(--bg-blue) !important; }
    
    /* Conteneur principal */
    .search-container {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 20px;
        padding: 3rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(30, 58, 138, 0.1);
    }
    
    /* Titre principal */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Zone de recherche principale */
    .stTextArea textarea {
        min-height: 120px !important;
        font-size: 16px !important;
        border: 2px solid #e0f2fe !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--secondary-blue) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Compteur de documents */
    .doc-counter {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem 0;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 8px rgba(30, 58, 138, 0.05);
    }
    
    .doc-count-item {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 8px;
        border: 1px solid #dbeafe;
    }
    
    .doc-count-number {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .doc-count-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Badges de mode */
    .mode-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%);
        border: 1px solid #bfdbfe;
        border-radius: 20px;
        color: var(--primary-blue);
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .mode-badge.active {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border-color: var(--primary-blue);
    }
    
    /* Cartes de modules */
    .module-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        cursor: pointer;
        height: 100%;
        position: relative;
        overflow: hidden;
    }
    
    .module-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(30, 58, 138, 0.12);
        border-color: var(--secondary-blue);
    }
    
    .module-card.selected {
        border: 2px solid var(--secondary-blue);
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%);
    }
    
    .module-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .module-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .module-description {
        color: var(--text-secondary);
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    /* Indicateurs de statut */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-active {
        background: linear-gradient(135deg, #3b82f6 0%, #1e3a8a 100%);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    
    .status-ready {
        background: linear-gradient(135deg, #93c5fd 0%, #60a5fa 100%);
    }
    
    .status-processing {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Historique de recherche */
    .search-history-item {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .search-history-item:hover {
        background: var(--bg-blue);
        border-color: var(--secondary-blue);
    }
    
    /* Instructions de recherche */
    .search-instructions {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    
    .instruction-item {
        display: flex;
        align-items: center;
        margin-bottom: 0.75rem;
        color: var(--text-secondary);
    }
    
    .instruction-code {
        background: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-family: monospace;
        color: var(--primary-blue);
        border: 1px solid #dbeafe;
        margin: 0 0.5rem;
    }
    
    /* Criticalité avec dégradés de bleu */
    .criticality-high {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
    }
    
    .criticality-medium {
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
    }
    
    .criticality-low {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        color: var(--primary-blue);
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Fonction de chargement paresseux des modules
@st.cache_resource
def load_module(module_name):
    """Charge un module de manière paresseuse"""
    try:
        module_path = Path(f"modules/{module_name}.py")
        if not module_path.exists():
            module_path = Path(f"modules/{module_name.replace('-', '_')}.py")
        
        if module_path.exists():
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement du module {module_name}: {str(e)}")
        return None

# Fonction pour compter les documents avec cache
@st.cache_data(ttl=300)
def count_documents():
    """Compte les documents locaux et dans les containers Azure"""
    counts = {'local': 0, 'containers': {}}
    
    # Documents locaux
    local_docs_path = Path("documents")
    if local_docs_path.exists():
        counts['local'] = sum(1 for f in local_docs_path.rglob("*") if f.is_file())
    
    # Simulation containers Azure
    counts['containers'] = {
        'juridique': 156,
        'expertises': 89,
        'procedures': 234,
        'correspondances': 412,
        'factures': 98
    }
    
    return counts

# Définition des modules
MODULES = {
    'analyse_contradictions': {
        'title': 'Analyse des Contradictions',
        'icon': '🔍',
        'description': 'Détectez automatiquement les incohérences entre vos documents',
        'tags': ['analyse', 'contradictions', 'cohérence']
    },
    'synthese_chronologique': {
        'title': 'Synthèse Chronologique',
        'icon': '📅',
        'description': 'Créez des chronologies détaillées de vos affaires',
        'tags': ['timeline', 'chronologie', 'dates']
    },
    'extraction_preuves': {
        'title': 'Extraction de Preuves',
        'icon': '📋',
        'description': 'Identifiez et organisez les éléments probants',
        'tags': ['preuves', 'extraction', 'classification']
    },
    'analyse_risques': {
        'title': 'Analyse des Risques',
        'icon': '⚠️',
        'description': 'Évaluez les risques juridiques de vos dossiers',
        'tags': ['risques', 'évaluation', 'alertes']
    },
    'generation_documents': {
        'title': 'Génération de Documents',
        'icon': '📝',
        'description': 'Créez automatiquement vos documents juridiques',
        'tags': ['génération', 'documents', 'modèles']
    },
    'recherche_jurisprudence': {
        'title': 'Recherche Jurisprudence',
        'icon': '⚖️',
        'description': 'Trouvez rapidement la jurisprudence pertinente',
        'tags': ['jurisprudence', 'recherche', 'précédents']
    }
}

# Parser de requête avancée
def parse_advanced_query(query):
    """Parse une requête avec syntaxe avancée (@container, opérateurs, etc.)"""
    result = {
        'container': None,
        'modules': [],
        'terms': [],
        'operators': [],
        'ai_model': st.session_state.ai_model,
        'raw_query': query
    }
    
    # Détection du container (@xxx)
    import re
    container_match = re.match(r'@(\w+)\s*,?\s*(.*)', query)
    if container_match:
        result['container'] = container_match.group(1)
        query = container_match.group(2)
        st.session_state.active_container = result['container']
    
    # Détection des modules (#module)
    module_matches = re.findall(r'#(\w+)', query)
    result['modules'] = module_matches
    for module in module_matches:
        query = query.replace(f'#{module}', '')
    
    # Extraction des termes et opérateurs
    for op in ['ET', 'OU', 'SAUF']:
        if op in query:
            result['operators'].append(op)
    
    result['terms'] = [t.strip() for t in query.split() if t.strip() and t not in ['ET', 'OU', 'SAUF']]
    
    return result

# Barre latérale
with st.sidebar:
    st.markdown("## ⚖️ Nexora Law IA")
    
    # Mode de recherche
    st.markdown("### 🔍 Mode de recherche")
    search_mode = st.radio(
        "",
        ["🌐 Recherche globale", "📁 Dans un container", "🔧 Modules spécifiques"],
        index=0,
        label_visibility="collapsed"
    )
    
    if search_mode == "📁 Dans un container":
        container = st.selectbox(
            "Container actif",
            list(count_documents()['containers'].keys()),
            help="Sélectionnez un container pour limiter la recherche"
        )
        st.session_state.active_container = container
    
    elif search_mode == "🔧 Modules spécifiques":
        st.markdown("Sélectionnez les modules :")
        for key, module in MODULES.items():
            if st.checkbox(f"{module['icon']} {module['title']}", key=f"cb_{key}"):
                if key not in st.session_state.selected_modules:
                    st.session_state.selected_modules.append(key)
            else:
                if key in st.session_state.selected_modules:
                    st.session_state.selected_modules.remove(key)
    
    # Modèle IA
    st.markdown("### 🤖 Modèle IA")
    ai_model = st.selectbox(
        "",
        ["claude-opus-4", "gpt-4-turbo", "multi-ia"],
        index=0,
        label_visibility="collapsed",
        help="Sélectionnez le modèle d'IA à utiliser"
    )
    st.session_state.ai_model = ai_model
    
    # Historique de recherche
    st.markdown("### 📜 Historique récent")
    if st.session_state.search_history:
        for i, search in enumerate(st.session_state.search_history[-5:]):
            if st.button(f"🔄 {search[:30]}...", key=f"history_{i}"):
                st.session_state.search_query = search
    else:
        st.info("Aucune recherche récente")
    
    # Statistiques
    st.markdown("### 📊 Statistiques")
    doc_counts = count_documents()
    total_docs = doc_counts['local'] + sum(doc_counts['containers'].values())
    st.metric("Total documents", f"{total_docs:,}")
    st.metric("Containers actifs", len(doc_counts['containers']))
    
    # Instructions
    with st.expander("💡 Syntaxe avancée"):
        st.markdown("""
        **Recherche par container :**
        - `@juridique, contrat de bail` 
        
        **Recherche dans modules :**
        - `#contradictions témoin`
        
        **Opérateurs logiques :**
        - `préjudice ET moral`
        - `accident SAUF voiture`
        
        **Combinaisons :**
        - `@expertises, #risques accident`
        """)

# Interface principale
if st.session_state.active_module:
    # Affichage d'un module spécifique
    module = load_module(st.session_state.active_module)
    if module and hasattr(module, 'run'):
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if st.button("← Retour", key="back_button"):
                st.session_state.active_module = None
                st.rerun()
        
        module.run()
else:
    # Page d'accueil
    st.markdown('<h1 class="main-title">Nexora Law IA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Assistant juridique intelligent propulsé par Claude Opus 4</p>', unsafe_allow_html=True)
    
    # Conteneur de recherche principal
    with st.container():
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        
        # Zone de recherche
        search_query = st.text_area(
            "",
            placeholder="Posez votre question juridique ou utilisez la syntaxe avancée...\n\nExemples :\n• Quelles sont les contradictions entre les témoignages ?\n• @expertises, analyse des risques financiers\n• #jurisprudence responsabilité civile accident",
            height=120,
            key="main_search",
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_button = st.button(
                "🔍 Rechercher avec Claude Opus 4",
                type="primary",
                use_container_width=True,
                disabled=not search_query
            )
        with col2:
            if st.button("🎯 Recherche guidée", use_container_width=True):
                st.session_state.show_guided_search = True
        with col3:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        
        # Modes actifs
        if st.session_state.active_container or st.session_state.selected_modules:
            st.markdown("**Modes actifs :**")
            if st.session_state.active_container:
                st.markdown(f'<span class="mode-badge active">📁 @{st.session_state.active_container}</span>', unsafe_allow_html=True)
            for module in st.session_state.selected_modules:
                module_info = MODULES.get(module, {})
                st.markdown(f'<span class="mode-badge active">{module_info.get("icon", "")} {module_info.get("title", module)}</span>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Traitement de la recherche
    if search_button and search_query:
        st.session_state.search_history.append(search_query)
        parsed_query = parse_advanced_query(search_query)
        
        with st.spinner(f"🔍 Analyse en cours avec {st.session_state.ai_model}..."):
            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress.progress(i + 1)
            
            # Résultats simulés
            st.success("✅ Recherche terminée !")
            
            # Affichage des résultats selon le contexte
            if parsed_query['container']:
                st.info(f"📁 Recherche dans le container **{parsed_query['container']}**")
            
            if parsed_query['modules']:
                st.info(f"🔧 Modules ciblés : {', '.join(parsed_query['modules'])}")
            
            # Suggestions de modules pertinents
            st.markdown("### 🎯 Actions suggérées")
            
            cols = st.columns(3)
            suggested_modules = ['analyse_contradictions', 'synthese_chronologique', 'extraction_preuves']
            
            for idx, module_key in enumerate(suggested_modules):
                with cols[idx]:
                    module_info = MODULES[module_key]
                    if st.button(
                        f"{module_info['icon']} {module_info['title']}",
                        key=f"suggest_{module_key}",
                        use_container_width=True,
                        help=module_info['description']
                    ):
                        st.session_state.active_module = module_key
                        st.rerun()
    
    # Compteur de documents
    doc_counts = count_documents()
    st.markdown('<div class="doc-counter">', unsafe_allow_html=True)
    
    cols = st.columns(len(doc_counts['containers']) + 1)
    
    with cols[0]:
        st.markdown(f'''
        <div class="doc-count-item">
            <div class="doc-count-number">{doc_counts['local']:,}</div>
            <div class="doc-count-label">📁 Documents locaux</div>
        </div>
        ''', unsafe_allow_html=True)
    
    for idx, (container, count) in enumerate(doc_counts['containers'].items(), 1):
        with cols[idx]:
            clickable = st.button(
                "",
                key=f"container_btn_{container}",
                use_container_width=True,
                help=f"Cliquer pour rechercher dans {container}"
            )
            st.markdown(f'''
            <div class="doc-count-item">
                <div class="doc-count-number">{count:,}</div>
                <div class="doc-count-label">☁️ {container.capitalize()}</div>
            </div>
            ''', unsafe_allow_html=True)
            if clickable:
                st.session_state.active_container = container
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Grille des modules
    st.markdown("### 🚀 Modules disponibles")
    
    # Filtre rapide
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_text = st.text_input("🔍 Filtrer les modules", placeholder="Ex: contradiction, chronologie...")
    with col2:
        show_all = st.checkbox("Afficher tout", value=True)
    
    # Affichage des modules
    cols = st.columns(3)
    module_index = 0
    
    for module_key, module_info in MODULES.items():
        # Filtrage
        if filter_text and filter_text.lower() not in module_info['title'].lower() and filter_text.lower() not in module_info['description'].lower():
            continue
        
        with cols[module_index % 3]:
            # Carte de module
            selected = module_key in st.session_state.selected_modules
            
            card_content = f"""
            <div class="module-card {'selected' if selected else ''}">
                <span class="status-indicator {'status-active' if selected else 'status-ready'}"></span>
                <div class="module-icon">{module_info['icon']}</div>
                <div class="module-title">{module_info['title']}</div>
                <div class="module-description">{module_info['description']}</div>
            </div>
            """
            
            if st.button(
                card_content,
                key=f"module_{module_key}",
                use_container_width=True,
                help=f"Tags: {', '.join(module_info.get('tags', []))}",
                disabled=False
            ):
                st.session_state.active_module = module_key
                st.rerun()
            
        module_index += 1
    
    # Section d'instructions détaillées
    with st.expander("📚 Guide d'utilisation avancé", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🔍 Syntaxe de recherche
            
            **Recherche par container :**
            - `@juridique` : recherche dans le container juridique
            - `@expertises, accident` : recherche "accident" dans les expertises
            
            **Recherche par module :**
            - `#contradictions` : utilise le module d'analyse des contradictions
            - `#timeline 2024` : génère une chronologie pour 2024
            
            **Opérateurs logiques :**
            - `ET` : tous les termes doivent être présents
            - `OU` : au moins un terme doit être présent
            - `SAUF` : exclut les documents contenant ce terme
            """)
        
        with col2:
            st.markdown("""
            ### 🎯 Exemples concrets
            
            **Recherches simples :**
            - `responsabilité civile accident`
            - `préjudice moral ET corporel`
            
            **Recherches avancées :**
            - `@expertises, #risques accident SAUF voiture`
            - `@juridique, #contradictions témoins ET 2024`
            
            **Multi-containers :**
            - `@juridique @expertises, analyse comparative`
            - `#timeline @procedures, année 2024`
            """)

# Footer avec statut
st.markdown("---")
cols = st.columns([1, 2, 1])
with cols[1]:
    st.markdown(
        f'<div style="text-align: center; color: #94a3b8;">Nexora Law IA v2.0 | Modèle actif : {st.session_state.ai_model} | {datetime.now().strftime("%H:%M")}</div>',
        unsafe_allow_html=True
    )

# Initialisation complète différée
if not st.session_state.initialized:
    st.session_state.initialized = True