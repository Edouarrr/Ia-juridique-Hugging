# enhanced_ui.py
"""
Interface utilisateur optimisée pour l'application juridique
Amélioration de l'UX, du design et de la fluidité
"""

import time
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

# Configuration de la page avec un design moderne
st.set_page_config(
    page_title="IA Juridique Pro",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un design moderne et fluide
def load_custom_css():
    st.markdown("""
    <style>
    /* Palette de couleurs professionnelle */
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
    
    /* Design général plus moderne */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Sidebar améliorée */
    .css-1d391kg {
        background-color: var(--secondary-color);
        border-right: 1px solid var(--border-color);
    }
    
    /* Barre de recherche personnalisée */
    .search-container {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 30px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .search-container:hover {
        border-color: var(--primary-color);
        box-shadow: 0 4px 12px rgba(26,115,232,0.15);
    }
    
    /* Boutons modernes */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        background-color: #1557b0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    /* Cards modernes */
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        height: 100%;
        cursor: pointer;
        border: 2px solid transparent;
    }
    
    .feature-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
        border-color: var(--primary-color);
    }
    
    /* Métriques améliorées */
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        transform: scale(1.02);
    }
    
    /* Navigation tabs moderne */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--secondary-color);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Animations fluides */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Amélioration des inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid var(--border-color);
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(26,115,232,0.1);
    }
    
    /* Quick action buttons */
    .quick-action {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        background: var(--hover-color);
        border-radius: 20px;
        margin: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid transparent;
    }
    
    .quick-action:hover {
        background: var(--primary-color);
        color: white;
        transform: scale(1.05);
    }
    
    /* Header moderne */
    .main-header {
        background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%);
        color: white;
        padding: 40px;
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(26,115,232,0.2);
    }
    
    /* Notifications */
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }
    </style>
    """, unsafe_allow_html=True)

def create_search_interface():
    """Crée une interface de recherche améliorée avec soumission sur Entrée"""
    
    # JavaScript pour gérer la soumission avec Entrée
    search_js = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Attendre que Streamlit charge complètement
        setTimeout(function() {
            const textarea = document.querySelector('.stTextArea textarea');
            if (textarea) {
                textarea.addEventListener('keydown', function(event) {
                    // Détecter Entrée sans modificateur
                    if (event.key === 'Enter' && !event.shiftKey && !event.ctrlKey && !event.metaKey) {
                        event.preventDefault();
                        
                        // Trouver et cliquer sur le bouton de recherche
                        const searchButton = document.querySelector('[data-testid="search-button"]');
                        if (searchButton) {
                            searchButton.click();
                        }
                    }
                });
                
                // Focus automatique sur la zone de recherche
                textarea.focus();
            }
        }, 500);
    });
    </script>
    """
    
    # Conteneur de recherche avec style
    st.markdown('<div class="search-container animate-in">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Zone de texte de 4 lignes
        query = st.text_area(
            "",
            placeholder="💡 Décrivez votre besoin juridique...\n\nExemples :\n• Rédiger des conclusions pour une affaire de...\n• Rechercher la jurisprudence sur...\n• Analyser les risques dans...",
            height=100,  # 4 lignes environ
            key="main_search",
            help="Appuyez sur Entrée pour lancer la recherche"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Espacement
        search_clicked = st.button(
            "🔍 Rechercher",
            key="search-button",
            use_container_width=True,
            type="primary"
        )
    
    # Suggestions rapides
    st.markdown("**Suggestions rapides :**")
    col1, col2, col3, col4 = st.columns(4)
    
    suggestions = [
        ("📝 Conclusions", "Rédiger des conclusions de défense"),
        ("⚖️ Jurisprudence", "Rechercher jurisprudence Cass. civ."),
        ("📊 Analyse", "Analyser les risques juridiques"),
        ("👥 Plaidoirie", "Préparer une plaidoirie de 30 min")
    ]
    
    for i, (col, (icon_text, suggestion)) in enumerate(zip([col1, col2, col3, col4], suggestions)):
        with col:
            if st.button(icon_text, key=f"quick_{i}", use_container_width=True):
                st.session_state.main_search = suggestion
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Injecter le JavaScript
    components.html(search_js, height=0)
    
    return query, search_clicked

def create_modern_sidebar():
    """Crée une sidebar moderne avec navigation intuitive"""
    
    with st.sidebar:
        # Logo et titre
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #1a73e8; margin: 0;">⚖️ IA Juridique</h1>
            <p style="color: #5f6368; margin: 5px 0;">Assistant Juridique Intelligent</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation principale avec icônes
        st.markdown("### 🧭 Navigation")
        
        menu_items = {
            "🏠 Accueil": "home",
            "📝 Rédaction": "redaction",
            "🔍 Recherche": "recherche",
            "📊 Analyse": "analyse",
            "📁 Documents": "documents",
            "⚙️ Paramètres": "settings"
        }
        
        for label, key in menu_items.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()
        
        st.markdown("---")
        
        # Actions rapides
        st.markdown("### ⚡ Actions rapides")
        
        if st.button("➕ Nouveau document", use_container_width=True):
            st.session_state.show_new_doc = True
            
        if st.button("📤 Importer fichiers", use_container_width=True):
            st.session_state.show_import = True
            
        if st.button("💾 Sauvegarder session", use_container_width=True):
            save_session()
        
        st.markdown("---")
        
        # Statistiques
        st.markdown("### 📈 Statistiques du jour")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", "12", "+3")
        with col2:
            st.metric("Recherches", "24", "+5")
        
        # Mode d'affichage
        st.markdown("---")
        st.markdown("### 🎨 Préférences")
        
        dark_mode = st.toggle("Mode sombre", key="dark_mode")
        compact_view = st.toggle("Vue compacte", key="compact_view")
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style="text-align: center; color: #5f6368; font-size: 12px;">
                v2.0 | Dernière mise à jour<br>
                {0}
            </div>
            """.format(datetime.now().strftime("%d/%m/%Y")),
            unsafe_allow_html=True
        )

def create_main_dashboard():
    """Crée le tableau de bord principal avec des cards modernes"""
    
    # Header principal
    st.markdown("""
    <div class="main-header animate-in">
        <h1 style="margin: 0; font-size: 2.5em;">Bienvenue dans votre espace juridique</h1>
        <p style="margin: 10px 0; opacity: 0.9; font-size: 1.2em;">
            Tous vos outils juridiques intelligents en un seul endroit
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("📄 Documents actifs", "156", "+12 cette semaine"),
        ("⚖️ Affaires en cours", "23", "+2 nouvelles"),
        ("🎯 Tâches du jour", "8", "3 urgentes"),
        ("⏱️ Temps économisé", "42h", "ce mois")
    ]
    
    for col, (label, value, delta) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-container animate-in">
                <h4 style="margin: 0; color: #5f6368;">{label}</h4>
                <h2 style="margin: 5px 0; color: #1a73e8;">{value}</h2>
                <p style="margin: 0; color: #34a853; font-size: 0.9em;">{delta}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Fonctionnalités principales en cards
    st.markdown("### 🚀 Fonctionnalités principales")
    
    col1, col2, col3 = st.columns(3)
    
    features = [
        {
            "col": col1,
            "icon": "📝",
            "title": "Rédaction intelligente",
            "desc": "Générez des documents juridiques en quelques clics",
            "features": ["Conclusions", "Assignations", "Plaidoiries", "Mémoires"],
            "action": "redaction"
        },
        {
            "col": col2,
            "icon": "🔍",
            "title": "Recherche avancée",
            "desc": "Trouvez instantanément jurisprudences et doctrines",
            "features": ["Judilibre", "Légifrance", "Base interne", "IA générative"],
            "action": "recherche"
        },
        {
            "col": col3,
            "icon": "📊",
            "title": "Analyse & Insights",
            "desc": "Comprenez vos dossiers avec l'IA",
            "features": ["Risques", "Timeline", "Mapping", "Synthèse"],
            "action": "analyse"
        }
    ]
    
    for feature in features:
        with feature["col"]:
            if st.button(
                "",
                key=f"feature_{feature['action']}",
                use_container_width=True,
                help=f"Accéder à {feature['title']}"
            ):
                st.session_state.current_page = feature["action"]
                st.rerun()
            
            # Contenu de la card (en HTML pour le style)
            st.markdown(f"""
            <div class="feature-card">
                <h2 style="margin: 0; color: #1a73e8;">{feature['icon']} {feature['title']}</h2>
                <p style="color: #5f6368; margin: 10px 0;">{feature['desc']}</p>
                <div style="margin-top: 15px;">
                    {''.join([f'<span class="quick-action">{f}</span>' for f in feature['features']])}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Section activité récente
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📅 Activité récente")
    
    tab1, tab2, tab3 = st.tabs(["📄 Documents récents", "🔍 Recherches", "📝 Brouillons"])
    
    with tab1:
        recent_docs = [
            ("Conclusions défense - Affaire Martin", "Il y a 2 heures", "En cours"),
            ("Assignation SARL Tech", "Hier", "Finalisé"),
            ("Plaidoirie audience 15/03", "Il y a 3 jours", "À réviser")
        ]
        
        for doc, time, status in recent_docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{doc}**")
            with col2:
                st.caption(time)
            with col3:
                if status == "En cours":
                    st.markdown("🟡 " + status)
                elif status == "Finalisé":
                    st.markdown("🟢 " + status)
                else:
                    st.markdown("🔵 " + status)
    
    with tab2:
        st.info("Vos dernières recherches apparaîtront ici")
    
    with tab3:
        st.info("Vos brouillons en cours apparaîtront ici")

def create_floating_help():
    """Crée un bouton d'aide flottant"""
    
    st.markdown("""
    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
        <button style="
            background: #1a73e8;
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        " onclick="alert('Aide : Utilisez la barre de recherche pour décrire votre besoin. Appuyez sur Entrée pour lancer la recherche.')">
            ?
        </button>
    </div>
    """, unsafe_allow_html=True)

def save_session():
    """Sauvegarde la session actuelle"""
    st.toast("✅ Session sauvegardée avec succès!", icon="✅")

# Fonction principale pour intégrer dans votre app.py
def enhanced_main_interface():
    """Interface principale améliorée"""
    
    # Charger le CSS personnalisé
    load_custom_css()
    
    # Créer la sidebar moderne
    create_modern_sidebar()
    
    # Interface principale
    if st.session_state.get('current_page', 'home') == 'home':
        # Barre de recherche améliorée
        query, search_clicked = create_search_interface()
        
        # Traiter la recherche
        if search_clicked or (query and st.session_state.get('last_query', '') != query):
            st.session_state.last_query = query
            with st.spinner("🔍 Analyse de votre demande..."):
                time.sleep(0.5)  # Simulation
                st.success(f"✅ Recherche lancée pour : {query}")
                # Ici, appeler votre logique de traitement
        
        # Dashboard principal
        create_main_dashboard()
    
    elif st.session_state.get('current_page') == 'redaction':
        st.title("📝 Module de rédaction")
        # Votre code de rédaction ici
        
    elif st.session_state.get('current_page') == 'recherche':
        st.title("🔍 Module de recherche")
        # Votre code de recherche ici
        
    # Bouton d'aide flottant
    create_floating_help()

# Pour tester
if __name__ == "__main__":
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    enhanced_main_interface()