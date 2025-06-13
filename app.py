import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import time

# Configuration de la page
st.set_page_config(
    page_title="IA Juridique Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction CSS améliorée
def load_custom_css():
    st.markdown("""
    <style>
    /* Variables CSS pour les couleurs */
    :root {
        --primary-color: #1a73e8;
        --secondary-color: #f8f9fa;
        --accent-color: #34a853;
        --danger-color: #ea4335;
        --text-primary: #202124;
        --text-secondary: #5f6368;
        --border-color: #dadce0;
        --hover-color: #e8f0fe;
    }
    
    /* Barre de recherche améliorée */
    .main-search-container {
        background: white;
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 25px;
        margin: 20px 0 30px 0;
        border: 2px solid transparent;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .main-search-container:hover {
        border-color: var(--primary-color);
        box-shadow: 0 4px 20px rgba(26,115,232,0.15);
        transform: translateY(-2px);
    }
    
    /* Zone de texte personnalisée */
    .stTextArea textarea {
        font-size: 16px !important;
        line-height: 1.5 !important;
        padding: 12px 16px !important;
        border-radius: 12px !important;
        border: 2px solid #e0e0e0 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(26,115,232,0.1) !important;
        outline: none !important;
    }
    
    /* Boutons modernes */
    .stButton > button {
        background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(26,115,232,0.25);
        text-transform: none;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(26,115,232,0.35);
        background: linear-gradient(135deg, #1557b0 0%, #1a73e8 100%);
    }
    
    /* Cards modernes */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        position: relative;
        overflow: hidden;
        border: 1px solid #f0f0f0;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #1a73e8 0%, #34a853 100%);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        transform: translateY(-4px);
        border-color: var(--primary-color);
    }
    
    .feature-card:hover::before {
        transform: scaleX(1);
    }
    
    /* Métriques améliorées */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--primary-color);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .metric-card:hover::after {
        transform: scaleX(1);
    }
    
    /* Header moderne */
    .main-header {
        background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
        color: white;
        padding: 50px 40px;
        border-radius: 20px;
        margin-bottom: 40px;
        box-shadow: 0 6px 20px rgba(26,115,232,0.2);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.3; }
    }
    
    /* Quick actions */
    .quick-action-chip {
        display: inline-block;
        padding: 6px 16px;
        margin: 4px;
        background: var(--hover-color);
        border-radius: 20px;
        font-size: 14px;
        color: var(--text-primary);
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    
    .quick-action-chip:hover {
        background: var(--primary-color);
        color: white;
        transform: scale(1.05);
        border-color: var(--primary-color);
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Navigation sidebar moderne */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        padding-top: 2rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-search-container {
            padding: 20px;
        }
        
        .feature-card {
            margin-bottom: 20px;
        }
        
        .main-header {
            padding: 30px 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Fonction de recherche améliorée
def create_enhanced_search():
    """Barre de recherche améliorée avec soumission sur Entrée"""
    
    # JavaScript pour gérer Entrée
    search_js = """
    <script>
    // Fonction pour gérer la soumission avec Entrée
    function setupSearchHandler() {
        const checkTextarea = setInterval(function() {
            const textarea = document.querySelector('textarea[aria-label="search_query"]');
            if (textarea) {
                clearInterval(checkTextarea);
                
                textarea.addEventListener('keydown', function(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        
                        // Simuler un changement pour déclencher Streamlit
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        nativeInputValueSetter.call(textarea, textarea.value);
                        
                        const inputEvent = new Event('input', { bubbles: true });
                        textarea.dispatchEvent(inputEvent);
                        
                        // Cliquer sur le bouton de recherche
                        setTimeout(function() {
                            const buttons = document.querySelectorAll('button');
                            buttons.forEach(button => {
                                if (button.textContent.includes('Rechercher')) {
                                    button.click();
                                }
                            });
                        }, 100);
                    }
                });
                
                // Focus automatique
                textarea.focus();
            }
        }, 100);
    }
    
    // Lancer au chargement et après chaque rerun
    if (document.readyState === 'complete') {
        setupSearchHandler();
    } else {
        document.addEventListener('DOMContentLoaded', setupSearchHandler);
    }
    
    // Relancer après un rerun Streamlit
    const observer = new MutationObserver(setupSearchHandler);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    # Conteneur principal de recherche
    st.markdown('<div class="main-search-container animate-in">', unsafe_allow_html=True)
    
    # Titre et description
    st.markdown("### 🔍 Comment puis-je vous aider aujourd'hui ?")
    st.caption("Décrivez votre besoin juridique en langage naturel")
    
    # Layout en colonnes
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Zone de texte de 4 lignes
        query = st.text_area(
            "search_query",
            label_visibility="hidden",
            placeholder=(
                "💡 Exemples :\n"
                "• Rédiger des conclusions pour une affaire d'abus de biens sociaux\n"
                "• Rechercher la jurisprudence sur le préjudice moral\n"
                "• Analyser les risques dans un contrat de cession"
            ),
            height=120,  # 4-5 lignes
            key="search_query_main",
            help="Appuyez sur Entrée pour lancer la recherche (Shift+Entrée pour nouvelle ligne)"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Alignement vertical
        search_button = st.button(
            "🔍 Rechercher",
            use_container_width=True,
            type="primary",
            key="search_submit_btn"
        )
    
    # Suggestions rapides
    st.markdown("**Actions rapides :**")
    
    quick_actions = [
        ("📝 Rédiger conclusions", "Rédiger des conclusions de défense pour"),
        ("⚖️ Recherche jurisprudence", "Rechercher la jurisprudence de la Cour de cassation sur"),
        ("📊 Analyser risques", "Analyser les risques juridiques dans"),
        ("👥 Préparer plaidoirie", "Préparer une plaidoirie de 30 minutes sur"),
        ("📋 Créer bordereau", "Créer un bordereau de communication de pièces"),
        ("🔄 Comparer versions", "Comparer deux versions de")
    ]
    
    # Afficher les actions en grille
    cols = st.columns(3)
    for idx, (label, prefix) in enumerate(quick_actions):
        with cols[idx % 3]:
            if st.button(label, key=f"quick_action_{idx}", use_container_width=True):
                st.session_state.search_query_main = prefix + " "
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Injecter le JavaScript
    components.html(search_js, height=0)
    
    return query, search_button

# Sidebar améliorée
def create_enhanced_sidebar():
    """Sidebar moderne avec navigation fluide"""
    
    with st.sidebar:
        # Header avec logo
        st.markdown("""
        <div style="text-align: center; padding: 30px 10px 20px 10px; background: linear-gradient(180deg, #1a73e8 0%, #1557b0 100%); margin: -35px -35px 20px -35px; border-radius: 0 0 20px 20px;">
            <h1 style="color: white; margin: 0; font-size: 2em;">⚖️ IA Juridique</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0; font-size: 0.9em;">Assistant Intelligent</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation principale
        st.markdown("### 🧭 Navigation principale")
        
        # Utiliser un radio pour la navigation (plus fluide)
        pages = {
            "🏠 Tableau de bord": "dashboard",
            "📝 Rédaction": "redaction",
            "🔍 Recherche": "recherche",
            "📊 Analyse": "analyse",
            "📁 Documents": "documents",
            "👥 Clients": "clients",
            "⚙️ Paramètres": "settings"
        }
        
        # Navigation avec style personnalisé
        selected_page = st.radio(
            "Navigation",
            options=list(pages.keys()),
            label_visibility="collapsed",
            key="nav_radio"
        )
        
        if selected_page:
            st.session_state.current_view = pages[selected_page]
        
        st.markdown("---")
        
        # Outils rapides
        st.markdown("### ⚡ Outils rapides")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Nouveau", use_container_width=True):
                st.session_state.show_new_dialog = True
        with col2:
            if st.button("📤 Import", use_container_width=True):
                st.session_state.show_import_dialog = True
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("💾 Sauver", use_container_width=True):
                save_current_work()
        with col4:
            if st.button("🔄 Sync", use_container_width=True):
                sync_data()
        
        st.markdown("---")
        
        # Projets récents
        st.markdown("### 📂 Projets récents")
        
        recent_projects = [
            ("Affaire Martin c/ Dupont", "🟢 Actif"),
            ("Succession Leblanc", "🟡 En attente"),
            ("SARL Tech vs État", "🔵 En révision")
        ]
        
        for project, status in recent_projects:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(project, key=f"proj_{project}", use_container_width=True):
                    load_project(project)
            with col2:
                st.markdown(status)
        
        # Stats du jour
        st.markdown("---")
        st.markdown("### 📈 Aujourd'hui")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", "8", "+3")
        with col2:
            st.metric("Heures", "5.2h", "-0.8h")
        
        # Mode et préférences
        st.markdown("---")
        st.markdown("### 🎨 Préférences")
        
        # Mode sombre
        dark_mode = st.checkbox("🌙 Mode sombre", key="dark_mode_toggle")
        
        # Vue compacte
        compact = st.checkbox("📐 Vue compacte", key="compact_view_toggle")
        
        # Notifications
        notifs = st.checkbox("🔔 Notifications", value=True, key="notifs_toggle")

# Fonctions utilitaires
def save_current_work():
    """Sauvegarde le travail en cours"""
    with st.spinner("Sauvegarde..."):
        time.sleep(0.5)
    st.toast("✅ Travail sauvegardé avec succès !", icon="✅")

def sync_data():
    """Synchronise les données"""
    with st.spinner("Synchronisation..."):
        time.sleep(1)
    st.toast("🔄 Synchronisation terminée !", icon="🔄")

def load_project(project_name):
    """Charge un projet"""
    st.session_state.current_project = project_name
    st.toast(f"📂 Projet '{project_name}' chargé", icon="📂")
    st.rerun()

def process_search_query(query: str):
    """Traite la requête de recherche"""
    with st.container():
        st.markdown("### 📋 Résultats de votre recherche")
        st.info(f"🔍 Recherche en cours pour : **{query}**")
        
        # Simulation de traitement
        with st.spinner("Analyse de votre demande..."):
            time.sleep(1.5)
        
        # Résultats simulés
        st.success("✅ Analyse terminée !")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h4>📄 Documents pertinents trouvés</h4>
                <ul>
                    <li>Modèle de conclusions type</li>
                    <li>Jurisprudence récente</li>
                    <li>Articles de doctrine</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h4>💡 Suggestions d'actions</h4>
                <ul>
                    <li>Générer un brouillon</li>
                    <li>Analyser les risques</li>
                    <li>Comparer avec des cas similaires</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# Page Dashboard
def show_dashboard():
    # Header moderne
    st.markdown("""
    <div class="main-header animate-in">
        <h1 style="margin: 0;">Bienvenue dans votre espace juridique intelligent</h1>
        <p style="margin: 10px 0; opacity: 0.9;">
            Transformez votre pratique juridique avec l'intelligence artificielle
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barre de recherche améliorée
    query, search_clicked = create_enhanced_search()
    
    # Traitement de la recherche
    if search_clicked and query:
        process_search_query(query)
    
    # Métriques en cards
    st.markdown("### 📊 Vue d'ensemble")
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("📄 Documents", "156", "+12%", col1),
        ("⚖️ Affaires", "23", "+2", col2),
        ("⏱️ Temps économisé", "42h", "+15%", col3),
        ("🎯 Efficacité", "94%", "+3%", col4)
    ]
    
    for label, value, delta, col in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card animate-in">
                <h4 style="margin: 0; color: #5f6368; font-weight: normal;">{label}</h4>
                <h2 style="margin: 8px 0; color: #1a73e8;">{value}</h2>
                <p style="margin: 0; color: #34a853; font-size: 0.9em;">▲ {delta}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Sections principales
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🚀 Accès rapide aux fonctionnalités")
    
    # Cards des fonctionnalités
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card animate-in">
            <h3 style="color: #1a73e8; margin-top: 0;">📝 Rédaction intelligente</h3>
            <p style="color: #5f6368;">Générez tous vos documents juridiques avec l'IA</p>
            <div style="margin-top: 20px;">
                <span class="quick-action-chip">Conclusions</span>
                <span class="quick-action-chip">Assignations</span>
                <span class="quick-action-chip">Plaidoiries</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card animate-in" style="animation-delay: 0.1s;">
            <h3 style="color: #1a73e8; margin-top: 0;">🔍 Recherche augmentée</h3>
            <p style="color: #5f6368;">Trouvez instantanément jurisprudences et doctrines</p>
            <div style="margin-top: 20px;">
                <span class="quick-action-chip">Judilibre</span>
                <span class="quick-action-chip">Légifrance</span>
                <span class="quick-action-chip">IA</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card animate-in" style="animation-delay: 0.2s;">
            <h3 style="color: #1a73e8; margin-top: 0;">📊 Analyse avancée</h3>
            <p style="color: #5f6368;">Comprenez vos dossiers en profondeur</p>
            <div style="margin-top: 20px;">
                <span class="quick-action-chip">Risques</span>
                <span class="quick-action-chip">Timeline</span>
                <span class="quick-action-chip">Insights</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Page Rédaction
def show_redaction():
    st.title("📝 Module de rédaction juridique")
    
    # Type de document
    doc_type = st.selectbox(
        "Type de document à rédiger",
        ["Conclusions", "Assignation", "Plaidoirie", "Contrat", "Consultation", "Autre"]
    )
    
    # Zone de saisie
    st.markdown("### 📋 Informations sur l'affaire")
    
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Nom du client", placeholder="Ex: M. Martin")
        adversaire = st.text_input("Partie adverse", placeholder="Ex: SARL Dupont")
    
    with col2:
        juridiction = st.text_input("Juridiction", placeholder="Ex: TGI Paris")
        numero_rg = st.text_input("N° RG", placeholder="Ex: 23/12345")
    
    # Description de l'affaire
    st.markdown("### 📝 Description de l'affaire")
    description = st.text_area(
        "Décrivez les faits et vos objectifs",
        height=200,
        placeholder="Décrivez en détail les faits de l'affaire, les points juridiques importants et ce que vous souhaitez obtenir..."
    )
    
    # Bouton de génération
    if st.button("🚀 Générer le document", type="primary", use_container_width=True):
        with st.spinner("Génération en cours..."):
            time.sleep(2)
        st.success("✅ Document généré avec succès !")
        
        # Affichage du résultat simulé
        st.markdown("### 📄 Document généré")
        st.markdown("""
        <div class="feature-card">
            <h4>CONCLUSIONS POUR {}</h4>
            <p><strong>Pour :</strong> {}</p>
            <p><strong>Contre :</strong> {}</p>
            <p><strong>Devant :</strong> {}</p>
            <hr>
            <p>PLAISE AU TRIBUNAL</p>
            <p>[Contenu généré par l'IA...]</p>
        </div>
        """.format(client_name or "[Client]", client_name or "[Client]", 
                   adversaire or "[Adversaire]", juridiction or "[Juridiction]"), 
        unsafe_allow_html=True)

# Page Recherche
def show_recherche():
    st.title("🔍 Recherche juridique avancée")
    
    # Barre de recherche
    search_query = st.text_input(
        "Rechercher dans la jurisprudence et la doctrine",
        placeholder="Ex: responsabilité contractuelle dommages-intérêts"
    )
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        source = st.multiselect(
            "Sources",
            ["Cour de cassation", "Conseil d'État", "Cours d'appel", "Doctrine"]
        )
    with col2:
        date_range = st.date_input(
            "Période",
            value=(datetime(2020, 1, 1), datetime.now())
        )
    with col3:
        juridiction = st.selectbox(
            "Matière",
            ["Toutes", "Civil", "Pénal", "Commercial", "Social", "Administratif"]
        )
    
    if st.button("🔍 Lancer la recherche", type="primary"):
        with st.spinner("Recherche en cours..."):
            time.sleep(1.5)
        
        # Résultats simulés
        st.markdown("### 📚 Résultats trouvés : 47")
        
        for i in range(3):
            st.markdown(f"""
            <div class="feature-card" style="margin-bottom: 20px;">
                <h4>🏛️ Cass. Civ. 1ère, {15-i} janvier 2024, n°23-1234{i}</h4>
                <p><strong>Mots-clés :</strong> Responsabilité contractuelle, Préjudice, Réparation intégrale</p>
                <p>La Cour de cassation rappelle que le débiteur n'est tenu que des dommages et intérêts 
                qui ont été prévus ou qu'on a pu prévoir lors du contrat...</p>
                <div style="margin-top: 15px;">
                    <span class="quick-action-chip">Lire l'arrêt</span>
                    <span class="quick-action-chip">Citer</span>
                    <span class="quick-action-chip">Analyser</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Page Analyse
def show_analyse():
    st.title("📊 Analyse de documents juridiques")
    
    # Upload de fichier
    uploaded_file = st.file_uploader(
        "Télécharger un document à analyser",
        type=['pdf', 'docx', 'txt'],
        help="Formats acceptés : PDF, DOCX, TXT"
    )
    
    if uploaded_file:
        st.success(f"✅ Fichier '{uploaded_file.name}' chargé")
        
        # Options d'analyse
        st.markdown("### 🎯 Type d'analyse")
        
        col1, col2 = st.columns(2)
        with col1:
            analyses = st.multiselect(
                "Sélectionnez les analyses à effectuer",
                ["Résumé automatique", "Points clés", "Risques juridiques", 
                 "Jurisprudence citée", "Timeline des faits", "Parties prenantes"]
            )
        
        with col2:
            format_output = st.radio(
                "Format de sortie",
                ["Rapport détaillé", "Synthèse exécutive", "Points bullet"]
            )
        
        if st.button("🚀 Lancer l'analyse", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                time.sleep(2)
            
            st.markdown("### 📈 Résultats de l'analyse")
            
            # Résultats simulés
            if "Résumé automatique" in analyses:
                st.markdown("""
                <div class="feature-card">
                    <h4>📄 Résumé automatique</h4>
                    <p>Ce document concerne un litige commercial entre deux sociétés concernant 
                    l'exécution d'un contrat de prestation de services...</p>
                </div>
                """, unsafe_allow_html=True)
            
            if "Risques juridiques" in analyses:
                st.markdown("""
                <div class="feature-card">
                    <h4>⚠️ Risques identifiés</h4>
                    <ul>
                        <li>🔴 <strong>Risque élevé :</strong> Prescription potentielle de l'action</li>
                        <li>🟡 <strong>Risque moyen :</strong> Preuve du préjudice insuffisante</li>
                        <li>🟢 <strong>Risque faible :</strong> Compétence juridictionnelle</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

# Page Documents
def show_documents():
    st.title("📁 Gestion des documents")
    
    # Barre de recherche et filtres
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("Rechercher un document", placeholder="Nom, client, type...")
    with col2:
        filter_type = st.selectbox("Type", ["Tous", "Conclusions", "Contrats", "Courriers"])
    with col3:
        sort_by = st.selectbox("Trier par", ["Date ↓", "Date ↑", "Nom", "Client"])
    
    # Liste des documents simulés
    documents = [
        {"nom": "Conclusions_Martin_vs_Dupont.pdf", "date": "2024-01-15", "client": "Martin", "taille": "245 KB"},
        {"nom": "Contrat_cession_parts_SARL.docx", "date": "2024-01-14", "client": "Tech Corp", "taille": "128 KB"},
        {"nom": "Assignation_TGI_Paris.pdf", "date": "2024-01-12", "client": "Leblanc", "taille": "189 KB"},
    ]
    
    # Affichage en tableau
    for doc in documents:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
        with col1:
            st.markdown(f"📄 **{doc['nom']}**")
        with col2:
            st.text(doc['client'])
        with col3:
            st.text(doc['date'])
        with col4:
            st.text(doc['taille'])
        with col5:
            if st.button("⬇️", key=f"dl_{doc['nom']}"):
                st.toast(f"Téléchargement de {doc['nom']}...")

# Page Clients
def show_clients():
    st.title("👥 Gestion des clients")
    
    # Ajout d'un nouveau client
    with st.expander("➕ Ajouter un nouveau client"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom", placeholder="Nom du client ou de la société")
            email = st.text_input("Email", placeholder="email@exemple.com")
        with col2:
            telephone = st.text_input("Téléphone", placeholder="01 23 45 67 89")
            type_client = st.selectbox("Type", ["Particulier", "Entreprise", "Association"])
        
        if st.button("Enregistrer le client", type="primary"):
            st.success("✅ Client enregistré avec succès !")
    
    # Liste des clients
    st.markdown("### 📋 Liste des clients")
    
    clients = [
        {"nom": "Martin Jean", "type": "Particulier", "affaires": 3, "dernier_contact": "2024-01-10"},
        {"nom": "SARL Tech Corp", "type": "Entreprise", "affaires": 5, "dernier_contact": "2024-01-15"},
        {"nom": "Association Envol", "type": "Association", "affaires": 2, "dernier_contact": "2024-01-08"},
    ]
    
    for client in clients:
        st.markdown(f"""
        <div class="feature-card" style="margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0;">{client['nom']}</h4>
                    <p style="margin: 5px 0; color: #5f6368;">
                        {client['type']} • {client['affaires']} affaires • Dernier contact : {client['dernier_contact']}
                    </p>
                </div>
                <div>
                    <span class="quick-action-chip">Voir détails</span>
                    <span class="quick-action-chip">Nouvelle affaire</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Page Paramètres
def show_settings():
    st.title("⚙️ Paramètres")
    
    # Tabs pour les différentes sections
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profil", "🔐 Sécurité", "🔔 Notifications", "💳 Abonnement"])
    
    with tab1:
        st.markdown("### Informations personnelles")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Nom", value="Maître Dupont")
            st.text_input("Email", value="contact@cabinet-dupont.fr")
        with col2:
            st.text_input("Cabinet", value="Cabinet Dupont & Associés")
            st.text_input("Barreau", value="Paris")
        
        if st.button("Enregistrer les modifications", type="primary"):
            st.success("✅ Profil mis à jour !")
    
    with tab2:
        st.markdown("### Sécurité du compte")
        st.checkbox("Authentification à deux facteurs", value=True)
        st.checkbox("Notifications de connexion", value=True)
        
        if st.button("Changer le mot de passe"):
            st.info("Un email vous a été envoyé pour réinitialiser votre mot de passe")
    
    with tab3:
        st.markdown("### Préférences de notifications")
        st.checkbox("Notifications par email", value=True)
        st.checkbox("Rappels d'échéances", value=True)
        st.checkbox("Mises à jour juridiques", value=False)
        st.checkbox("Newsletter mensuelle", value=True)
    
    with tab4:
        st.markdown("### Votre abonnement")
        st.info("**Plan actuel :** Premium")
        st.metric("Utilisation ce mois", "127 / 500 requêtes", "25%")
        
        st.markdown("""
        <div class="feature-card">
            <h4>✨ Avantages Premium</h4>
            <ul>
                <li>500 requêtes IA par mois</li>
                <li>Accès illimité aux modèles</li>
                <li>Support prioritaire</li>
                <li>Exports illimités</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# Fonction principale
def main():
    """Fonction principale avec UI améliorée"""
    
    # Charger le CSS amélioré
    load_custom_css()
    
    # Initialiser session state si nécessaire
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'dashboard'
    
    # Sidebar améliorée
    create_enhanced_sidebar()
    
    # Contenu principal selon la vue
    if st.session_state.current_view == 'dashboard':
        show_dashboard()
    elif st.session_state.current_view == 'redaction':
        show_redaction()
    elif st.session_state.current_view == 'recherche':
        show_recherche()
    elif st.session_state.current_view == 'analyse':
        show_analyse()
    elif st.session_state.current_view == 'documents':
        show_documents()
    elif st.session_state.current_view == 'clients':
        show_clients()
    elif st.session_state.current_view == 'settings':
        show_settings()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: gray;'>⚖️ IA Juridique Pro - Votre assistant juridique intelligent</p>",
        unsafe_allow_html=True
    )

# Point d'entrée
if __name__ == "__main__":
    main()