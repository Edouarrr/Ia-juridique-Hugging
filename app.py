# integrate_enhanced_ui.py
"""
Guide pour intégrer les améliorations UX dans votre app.py existant
"""

# ========== ÉTAPE 1 : IMPORTS À AJOUTER ==========
# Ajoutez ces imports au début de votre app.py

import streamlit.components.v1 as components
import time
from datetime import datetime

# ========== ÉTAPE 2 : CONFIGURATION DE LA PAGE ==========
# Remplacez votre st.set_page_config actuel par :

st.set_page_config(
    page_title="IA Juridique Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ÉTAPE 3 : FONCTION CSS AMÉLIORÉE ==========
# Remplacez votre fonction load_custom_css() par celle-ci :

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
    
    /* Bouton principal (recherche) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
        min-height: 80px;
        font-size: 18px;
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
    
    /* Navigation sidebar moderne */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        padding-top: 2rem;
    }
    
    /* Boutons de navigation */
    .nav-button {
        width: 100%;
        text-align: left;
        padding: 12px 20px;
        margin: 4px 0;
        border-radius: 12px;
        transition: all 0.2s ease;
        background: transparent;
        border: none;
        cursor: pointer;
        font-size: 16px;
        color: var(--text-primary);
    }
    
    .nav-button:hover {
        background: var(--hover-color);
        padding-left: 25px;
    }
    
    .nav-button.active {
        background: var(--primary-color);
        color: white;
        font-weight: 600;
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

# ========== ÉTAPE 4 : FONCTION DE RECHERCHE AMÉLIORÉE ==========
# Remplacez votre fonction de recherche par celle-ci :

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

# ========== ÉTAPE 5 : SIDEBAR AMÉLIORÉE ==========
# Fonction pour une sidebar moderne

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

# ========== ÉTAPE 6 : FONCTIONS UTILITAIRES ==========

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

# ========== ÉTAPE 7 : INTÉGRATION DANS VOTRE app.py ==========
# Dans votre fonction main() ou là où vous gérez l'interface :

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
            with st.spinner("🤔 Analyse de votre demande..."):
                time.sleep(0.5)
                # Appeler votre logique existante ici
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
    
    # Autres vues...
    elif st.session_state.current_view == 'redaction':
        st.title("📝 Module de rédaction")
        # Votre code existant
        
    elif st.session_state.current_view == 'recherche':
        st.title("🔍 Module de recherche")
        # Votre code existant

# Fonction helper pour traiter les recherches
def process_search_query(query: str):
    """Traite la requête de recherche"""
    # Votre logique existante
    st.success(f"Recherche lancée pour : {query}")

# ========== EXEMPLE D'UTILISATION ==========
if __name__ == "__main__":
    main()