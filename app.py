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

# Fonction CSS améliorée avec style sobre
def load_custom_css():
    st.markdown("""
    <style>
    /* Variables CSS pour les couleurs sobres */
    :root {
        --primary-color: #4a5568;
        --secondary-color: #f7fafc;
        --accent-color: #5a67d8;
        --danger-color: #e53e3e;
        --text-primary: #2d3748;
        --text-secondary: #718096;
        --border-color: #e2e8f0;
        --hover-color: #edf2f7;
        --background-light: #f8f9fa;
    }
    
    /* Typography sobre */
    h1 { font-size: 1.75rem !important; color: var(--text-primary); }
    h2 { font-size: 1.5rem !important; color: var(--text-primary); }
    h3 { font-size: 1.25rem !important; color: var(--text-primary); }
    h4 { font-size: 1.1rem !important; color: var(--text-primary); }
    
    /* Barre de recherche sobre */
    .main-search-container {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        padding: 20px;
        margin: 15px 0 25px 0;
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }
    
    .main-search-container:hover {
        border-color: var(--accent-color);
        box-shadow: 0 2px 8px rgba(90,103,216,0.15);
    }
    
    /* Zone de texte sobre */
    .stTextArea textarea {
        font-size: 14px !important;
        line-height: 1.5 !important;
        padding: 10px 14px !important;
        border-radius: 6px !important;
        border: 1px solid #cbd5e0 !important;
        transition: all 0.2s ease !important;
        background-color: #fafafa !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 0 2px rgba(90,103,216,0.1) !important;
        outline: none !important;
        background-color: white !important;
    }
    
    /* Boutons sobres */
    .stButton > button {
        background: var(--accent-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-transform: none;
    }
    
    .stButton > button:hover {
        background: #4c51bf;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    /* Cards sobres */
    .feature-card {
        background: white;
        border-radius: 6px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
        border: 1px solid var(--border-color);
    }
    
    .feature-card:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Métriques sobres */
    .metric-card {
        background: var(--background-light);
        border-radius: 6px;
        padding: 18px;
        text-align: center;
        transition: all 0.2s ease;
        border: 1px solid var(--border-color);
    }
    
    .metric-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Header sobre */
    .main-header {
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
        color: white;
        padding: 30px 25px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-size: 1.5rem !important;
        margin: 0;
        font-weight: 600;
    }
    
    .main-header p {
        font-size: 0.95rem;
        opacity: 0.9;
        margin: 8px 0 0 0;
    }
    
    /* Quick actions sobres */
    .quick-action-chip {
        display: inline-block;
        padding: 5px 12px;
        margin: 3px;
        background: var(--hover-color);
        border-radius: 4px;
        font-size: 13px;
        color: var(--text-primary);
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid var(--border-color);
    }
    
    .quick-action-chip:hover {
        background: var(--accent-color);
        color: white;
        border-color: var(--accent-color);
    }
    
    /* Navigation sidebar sobre */
    .css-1d391kg {
        background: var(--background-light);
        padding-top: 1.5rem;
    }
    
    /* Mode @ sobre */
    .stTextArea textarea[data-mode="dossier"] {
        background-color: #f0f4ff !important;
        border-color: var(--accent-color) !important;
    }
    
    /* Résultats de recherche @ sobres */
    .dossier-result {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 12px 16px;
        margin: 6px 0;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    
    .dossier-result:hover {
        border-color: var(--accent-color);
        background: var(--hover-color);
        transform: translateX(3px);
    }
    
    /* Réduction générale des espacements */
    .block-container {
        padding-top: 2rem !important;
        max-width: 1200px !important;
    }
    
    .element-container {
        margin-bottom: 0.75rem !important;
    }
    
    /* Style sobre pour les métriques */
    [data-testid="metric-container"] {
        background: var(--background-light);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 1rem;
    }
    
    [data-testid="metric-container"] > div {
        font-size: 0.9rem !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 1.5rem !important;
        color: var(--accent-color);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-search-container {
            padding: 15px;
        }
        
        .feature-card {
            margin-bottom: 15px;
        }
        
        .main-header {
            padding: 20px 15px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Base de données simulée de dossiers
DOSSIERS_DB = [
    {"ref": "2024-001", "nom": "Martin c/ Dupont", "client": "Martin Jean", "type": "Civil", "statut": "En cours"},
    {"ref": "2024-002", "nom": "Succession Leblanc", "client": "Famille Leblanc", "type": "Succession", "statut": "En attente"},
    {"ref": "2024-003", "nom": "SARL Tech vs État", "client": "SARL Tech", "type": "Administratif", "statut": "Plaidoirie"},
    {"ref": "2023-156", "nom": "Divorce Moreau", "client": "Moreau Sophie", "type": "Famille", "statut": "Terminé"},
    {"ref": "2023-203", "nom": "Licenciement Durand", "client": "Durand Pierre", "type": "Social", "statut": "En cours"},
    {"ref": "ABS-2024", "nom": "Abus de biens sociaux SAS Finance", "client": "Partie civile", "type": "Pénal", "statut": "Instruction"},
    {"ref": "2024-045", "nom": "Contentieux construction Villa Azur", "client": "SCI Villa Azur", "type": "Construction", "statut": "Expertise"},
    {"ref": "2024-067", "nom": "Marque contrefaçon LuxBrand", "client": "LuxBrand SARL", "type": "Propriété intellectuelle", "statut": "En cours"},
    {"ref": "2023-412", "nom": "Accident circulation Bertrand", "client": "Bertrand Michel", "type": "Préjudice corporel", "statut": "Négociation"},
    {"ref": "REF-2024", "nom": "Référé commercial urgent", "client": "StartUp Tech", "type": "Commercial", "statut": "Urgent"},
]

# Fonction pour rechercher des dossiers
def search_dossiers(search_term):
    """Recherche dans la base de dossiers"""
    search_term = search_term.lower()
    results = []
    
    for dossier in DOSSIERS_DB:
        # Recherche dans tous les champs
        if (search_term in dossier["ref"].lower() or 
            search_term in dossier["nom"].lower() or 
            search_term in dossier["client"].lower() or
            search_term in dossier["type"].lower()):
            results.append(dossier)
    
    return results[:5]  # Limiter à 5 résultats

# Fonction pour analyser les requêtes en langage naturel
def analyze_natural_language_query(query):
    """Analyse la requête en langage naturel et détermine l'action à effectuer"""
    query_lower = query.lower()
    
    # Dictionnaire de mots-clés pour chaque module
    keywords = {
        'redaction': ['rédiger', 'écrire', 'créer', 'préparer', 'faire', 'conclusions', 'assignation', 
                     'plaidoirie', 'contrat', 'bordereau', 'document', 'courrier', 'lettre'],
        'recherche': ['rechercher', 'trouver', 'chercher', 'jurisprudence', 'arrêt', 'décision', 
                     'doctrine', 'légifrance', 'judilibre', 'cour de cassation', 'conseil d\'état'],
        'analyse': ['analyser', 'analyse', 'risques', 'étudier', 'examiner', 'comprendre', 
                   'évaluer', 'vérifier', 'contrôler'],
        'documents': ['documents', 'fichiers', 'pdf', 'télécharger', 'consulter', 'ouvrir', 
                     'mes documents', 'retrouver', 'accéder'],
        'clients': ['client', 'clients', 'contact', 'coordonnées', 'ajouter client', 
                   'nouveau client', 'gérer clients'],
        'dossiers': ['dossier', 'affaire', 'consulter dossier', 'voir dossier', 'ouvrir dossier',
                    'mes dossiers', 'dossiers en cours'],
        'help': ['aide', 'comment', 'où', 'quoi', 'pourquoi', 'expliquer', 'utiliser', 
                'fonctionnement', 'marche', 'faire pour', '?']
    }
    
    # Analyser la requête - vérifier d'abord les mots d'aide
    if any(word in query_lower for word in keywords['help']):
        # Vérifier si c'est une question sur une fonctionnalité spécifique
        for module, words in keywords.items():
            if module != 'help' and any(word in query_lower for word in words):
                return 'help', query
        return 'help', query
    
    # Ensuite vérifier les autres modules
    for module, words in keywords.items():
        if module != 'help':
            for word in words:
                if word in query_lower:
                    return module, query
    
    # Si aucune correspondance, retourner une recherche générale
    return 'general', query

# Fonction de recherche améliorée avec support @ et langage naturel
def create_enhanced_search():
    """Barre de recherche améliorée avec support @ pour les dossiers et langage naturel"""
    
    # JavaScript amélioré pour gérer @ et Entrée
    search_js = """
    <script>
    // Fonction pour gérer la recherche et l'autocomplétion
    function setupEnhancedSearch() {
        const checkTextarea = setInterval(function() {
            const textarea = document.querySelector('textarea[aria-label="search_query"]');
            if (textarea) {
                clearInterval(checkTextarea);
                
                // Variable pour stocker si on est en mode dossier
                let isDossierMode = false;
                
                // Écouter les changements de texte
                textarea.addEventListener('input', function(event) {
                    const value = textarea.value;
                    const lastChar = value[value.length - 1];
                    
                    // Détecter si on tape @
                    if (lastChar === '@') {
                        isDossierMode = true;
                        // Vous pouvez ajouter ici un indicateur visuel
                        textarea.style.borderColor = '#5a67d8';
                        textarea.style.backgroundColor = '#f0f4ff';
                    } else if (value.includes('@')) {
                        isDossierMode = true;
                    } else {
                        isDossierMode = false;
                        textarea.style.borderColor = '';
                        textarea.style.backgroundColor = '';
                    }
                });
                
                // Gérer la touche Entrée
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
    
    // Lancer au chargement
    if (document.readyState === 'complete') {
        setupEnhancedSearch();
    } else {
        document.addEventListener('DOMContentLoaded', setupEnhancedSearch);
    }
    
    // Relancer après un rerun Streamlit
    const observer = new MutationObserver(setupEnhancedSearch);
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """
    
    # Conteneur principal de recherche
    st.markdown('<div class="main-search-container">', unsafe_allow_html=True)
    
    # Titre et description
    st.markdown("#### 🔍 Comment puis-je vous aider ?")
    st.caption("Décrivez votre besoin en langage naturel ou tapez @ pour rechercher un dossier")
    
    # Layout en colonnes
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Zone de texte de 4 lignes
        query = st.text_area(
            "search_query",
            label_visibility="hidden",
            placeholder=(
                "💡 Exemples :\n"
                "• Comment rédiger des conclusions ? → Vous guide vers le module Rédaction\n"
                "• Où sont mes documents ? → Vous dirige vers vos fichiers\n"
                "• @Martin → Recherche les dossiers du client Martin"
            ),
            height=100,
            key="search_query_main",
            help="Posez votre question en français ou tapez @ pour rechercher un dossier"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Alignement vertical
        search_button = st.button(
            "🔍",
            use_container_width=True,
            type="primary",
            key="search_submit_btn"
        )
    
    # Détection du mode @ et affichage des suggestions
    if query and query.strip().startswith("@"):
        search_term = query[1:].strip()  # Enlever le @
        
        if search_term:  # Si il y a du texte après @
            # Rechercher les dossiers correspondants
            dossiers_found = search_dossiers(search_term)
            
            if dossiers_found:
                st.markdown("##### 📁 Dossiers trouvés")
                for dossier in dossiers_found:
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        if st.button(
                            f"📂 {dossier['ref']} - {dossier['nom']}", 
                            key=f"dossier_{dossier['ref']}",
                            use_container_width=True
                        ):
                            # Charger le dossier
                            st.session_state.current_dossier = dossier
                            st.session_state.search_query_main = ""
                            st.session_state.current_view = "dossier_detail"
                            st.rerun()
                    with col2:
                        st.markdown(f"<small>{dossier['client']}</small>", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"<small>{dossier['type']}</small>", unsafe_allow_html=True)
                    with col4:
                        # Badge de statut avec couleur
                        color = {
                            "En cours": "🟢",
                            "En attente": "🟡",
                            "Plaidoirie": "🔵",
                            "Terminé": "⚫",
                            "Instruction": "🔴",
                            "Expertise": "🟣",
                            "Négociation": "🟠",
                            "Urgent": "🔴"
                        }.get(dossier['statut'], "⚪")
                        st.markdown(f"<small>{color} {dossier['statut']}</small>", unsafe_allow_html=True)
            else:
                st.info("Aucun dossier trouvé. Essayez avec d'autres mots-clés.")
        else:
            st.info("💡 Tapez un mot-clé après @ : référence, nom du client, type d'affaire...")
    
    # Suggestions rapides (masquées en mode @)
    elif not (query and query.strip().startswith("@")):
        st.markdown("**Suggestions :**")
        
        quick_actions = [
            ("📝 Rédiger", "Comment rédiger des conclusions"),
            ("🔍 Rechercher", "Où trouver la jurisprudence"),
            ("📊 Analyser", "Comment analyser un contrat"),
            ("📁 Documents", "Où sont mes documents"),
            ("👥 Clients", "Comment ajouter un client"),
            ("❓ Aide", "Comment utiliser l'application")
        ]
        
        # Afficher les actions en grille
        cols = st.columns(3)
        for idx, (label, prefix) in enumerate(quick_actions):
            with cols[idx % 3]:
                if st.button(label, key=f"quick_action_{idx}", use_container_width=True):
                    st.session_state.search_query_main = prefix
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Injecter le JavaScript
    components.html(search_js, height=0)
    
    return query, search_button

# Sidebar améliorée
def create_enhanced_sidebar():
    """Sidebar sobre avec navigation fluide"""
    
    with st.sidebar:
        # Header avec logo
        st.markdown("""
        <div style="text-align: center; padding: 20px 10px 15px 10px; background: var(--accent-color); margin: -35px -35px 15px -35px; border-radius: 0 0 8px 8px;">
            <h2 style="color: white; margin: 0; font-size: 1.4em; font-weight: 600;">⚖️ IA Juridique</h2>
            <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 0.85em;">Assistant Professionnel</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation principale
        st.markdown("##### Navigation")
        
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
        st.markdown("##### Actions rapides")
        
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
        st.markdown("##### Dossiers récents")
        
        recent_projects = [
            ("Martin c/ Dupont", "🟢"),
            ("Succession Leblanc", "🟡"),
            ("SARL Tech vs État", "🔵")
        ]
        
        for project, status in recent_projects:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(project, key=f"proj_{project}", use_container_width=True):
                    load_project(project)
            with col2:
                st.markdown(status)
        
        # Stats du jour
        st.markdown("---")
        st.markdown("##### Statistiques")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", "8", "+3", label_visibility="visible")
        with col2:
            st.metric("Heures", "5.2h", "-0.8h", label_visibility="visible")

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
    """Traite la requête de recherche avec support @ et langage naturel"""
    
    # Vérifier si c'est une recherche de dossier avec @
    if query.strip().startswith("@"):
        search_term = query[1:].strip()
        dossiers_found = search_dossiers(search_term)
        
        if dossiers_found:
            st.markdown("#### 📁 Résultats de recherche de dossiers")
            for dossier in dossiers_found:
                st.markdown(f"""
                <div class="feature-card" style="margin-bottom: 12px; cursor: pointer;">
                    <h5 style="margin: 0;">📂 {dossier['ref']} - {dossier['nom']}</h5>
                    <p style="margin: 5px 0; font-size: 0.9em;"><strong>Client :</strong> {dossier['client']} | <strong>Type :</strong> {dossier['type']} | <strong>Statut :</strong> {dossier['statut']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Aucun dossier trouvé avec ces critères.")
    else:
        # Analyser la requête en langage naturel
        module, clean_query = analyze_natural_language_query(query)
        
        if module == 'help':
            # Afficher l'aide contextuelle
            st.markdown("#### ❓ Aide - Comment utiliser l'application")
            
            if 'rédiger' in query.lower() or 'écrire' in query.lower():
                st.info("Pour rédiger un document, utilisez le module **📝 Rédaction** dans le menu latéral.")
                st.markdown("""
                <div class="feature-card">
                    <h5>📝 Module Rédaction</h5>
                    <p>Le module de rédaction vous permet de :</p>
                    <ul style="font-size: 0.9em;">
                        <li>Créer des conclusions</li>
                        <li>Rédiger des assignations</li>
                        <li>Préparer des plaidoiries</li>
                        <li>Générer des contrats</li>
                    </ul>
                    <p style="font-size: 0.9em;"><strong>Accès :</strong> Menu latéral → 📝 Rédaction</p>
                </div>
                """, unsafe_allow_html=True)
                
            elif 'document' in query.lower() or 'fichier' in query.lower():
                st.info("Pour accéder à vos documents, utilisez le module **📁 Documents** dans le menu latéral.")
                st.markdown("""
                <div class="feature-card">
                    <h5>📁 Module Documents</h5>
                    <p>Le module Documents vous permet de :</p>
                    <ul style="font-size: 0.9em;">
                        <li>Consulter tous vos fichiers</li>
                        <li>Rechercher par nom ou type</li>
                        <li>Télécharger vos documents</li>
                        <li>Organiser par dossier</li>
                    </ul>
                    <p style="font-size: 0.9em;"><strong>Accès :</strong> Menu latéral → 📁 Documents</p>
                </div>
                """, unsafe_allow_html=True)
                
            elif 'jurisprudence' in query.lower() or 'recherche' in query.lower():
                st.info("Pour rechercher de la jurisprudence, utilisez le module **🔍 Recherche** dans le menu latéral.")
                st.markdown("""
                <div class="feature-card">
                    <h5>🔍 Module Recherche</h5>
                    <p>Le module Recherche vous donne accès à :</p>
                    <ul style="font-size: 0.9em;">
                        <li>Jurisprudence de la Cour de cassation</li>
                        <li>Décisions du Conseil d'État</li>
                        <li>Arrêts des cours d'appel</li>
                        <li>Articles de doctrine</li>
                    </ul>
                    <p style="font-size: 0.9em;"><strong>Accès :</strong> Menu latéral → 🔍 Recherche</p>
                </div>
                """, unsafe_allow_html=True)
            elif 'utiliser' in query.lower() or 'fonctionne' in query.lower():
                st.info("Je vais vous expliquer comment utiliser l'application.")
                st.markdown("""
                <div class="feature-card">
                    <h5>🎯 Guide d'utilisation rapide</h5>
                    <ol style="font-size: 0.9em;">
                        <li><strong>Navigation :</strong> Utilisez le menu latéral pour accéder aux modules</li>
                        <li><strong>Recherche intelligente :</strong> Posez vos questions en français dans la barre de recherche</li>
                        <li><strong>Accès rapide :</strong> Tapez @ suivi d'un nom pour trouver un dossier</li>
                        <li><strong>Actions :</strong> Cliquez sur les boutons d'action rapide pour les tâches courantes</li>
                    </ol>
                    <p style="font-size: 0.9em; margin-top: 10px;"><strong>💡 Astuce :</strong> 
                    La barre de recherche comprend vos questions et vous guide vers la bonne fonctionnalité !</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Aide générale
                st.markdown("""
            else:
                # Aide générale
                st.markdown("""
                <div class="feature-card">
                    <h5>🎯 Navigation dans l'application</h5>
                    <p style="font-size: 0.9em;">Voici les principaux modules disponibles :</p>
                    <ul style="font-size: 0.9em;">
                        <li><strong>🏠 Tableau de bord :</strong> Vue d'ensemble et recherche</li>
                        <li><strong>📝 Rédaction :</strong> Créer des documents juridiques</li>
                        <li><strong>🔍 Recherche :</strong> Jurisprudence et doctrine</li>
                        <li><strong>📊 Analyse :</strong> Analyser des documents</li>
                        <li><strong>📁 Documents :</strong> Gérer vos fichiers</li>
                        <li><strong>👥 Clients :</strong> Gérer vos contacts</li>
                    </ul>
                    <p style="font-size: 0.9em; margin-top: 10px;"><strong>💡 Astuce :</strong> Tapez @ suivi d'un nom pour rechercher un dossier</p>
                </div>
                """, unsafe_allow_html=True)
                <div class="feature-card">
                    <h5>🎯 Navigation dans l'application</h5>
                    <p style="font-size: 0.9em;">Voici les principaux modules disponibles :</p>
                    <ul style="font-size: 0.9em;">
                        <li><strong>🏠 Tableau de bord :</strong> Vue d'ensemble et recherche</li>
                        <li><strong>📝 Rédaction :</strong> Créer des documents juridiques</li>
                        <li><strong>🔍 Recherche :</strong> Jurisprudence et doctrine</li>
                        <li><strong>📊 Analyse :</strong> Analyser des documents</li>
                        <li><strong>📁 Documents :</strong> Gérer vos fichiers</li>
                        <li><strong>👥 Clients :</strong> Gérer vos contacts</li>
                    </ul>
                    <p style="font-size: 0.9em; margin-top: 10px;"><strong>💡 Astuce :</strong> Tapez @ suivi d'un nom pour rechercher un dossier</p>
                </div>
                """, unsafe_allow_html=True)
                
        elif module == 'redaction':
            st.info(f"Je vais vous aider à rédiger. Dirigez-vous vers le module **📝 Rédaction** dans le menu latéral.")
            if st.button("Aller au module Rédaction", type="primary"):
                st.session_state.current_view = 'redaction'
                st.rerun()
                
        elif module == 'recherche':
            st.info(f"Pour rechercher de la jurisprudence, utilisez le module **🔍 Recherche** dans le menu latéral.")
            if st.button("Aller au module Recherche", type="primary"):
                st.session_state.current_view = 'recherche'
                st.rerun()
                
        elif module == 'documents':
            st.info(f"Vos documents sont dans le module **📁 Documents** dans le menu latéral.")
            if st.button("Aller au module Documents", type="primary"):
                st.session_state.current_view = 'documents'
                st.rerun()
                
        elif module == 'clients':
            st.info(f"Pour gérer vos clients, utilisez le module **👥 Clients** dans le menu latéral.")
            if st.button("Aller au module Clients", type="primary"):
                st.session_state.current_view = 'clients'
                st.rerun()
                
        elif module == 'analyse':
            st.info(f"Pour analyser un document, utilisez le module **📊 Analyse** dans le menu latéral.")
            if st.button("Aller au module Analyse", type="primary"):
                st.session_state.current_view = 'analyse'
                st.rerun()
                
        else:
            # Recherche générale - Afficher des résultats pertinents
            with st.container():
                st.markdown("#### 📋 Résultats de votre recherche")
                st.info(f"🔍 Recherche : **{query}**")
                
                # Suggestions basées sur la requête
                st.markdown("##### 💡 Suggestions d'actions")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    <div class="feature-card">
                        <h5>📄 Documents suggérés</h5>
                        <ul style="font-size: 0.9em;">
                            <li>Modèles de documents</li>
                            <li>Jurisprudence pertinente</li>
                            <li>Articles de doctrine</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    st.markdown("""
                    <div class="feature-card">
                        <h5>🚀 Actions recommandées</h5>
                        <ul style="font-size: 0.9em;">
                            <li>Créer un nouveau document</li>
                            <li>Analyser un cas similaire</li>
                            <li>Consulter la jurisprudence</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

# Page détail d'un dossier
def show_dossier_detail():
    """Affiche le détail d'un dossier avec style sobre"""
    if 'current_dossier' not in st.session_state:
        st.error("Aucun dossier sélectionné")
        return
    
    dossier = st.session_state.current_dossier
    
    # Header du dossier
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 1.4rem;">📂 {dossier['ref']} - {dossier['nom']}</h1>
        <p style="margin: 8px 0; font-size: 0.9em;">
            Client : {dossier['client']} | Type : {dossier['type']} | Statut : {dossier['statut']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Onglets du dossier
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Résumé", "📄 Documents", "⏱️ Chronologie", "💬 Notes", "⚖️ Procédures"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h5>👤 Informations client</h5>
                <p style="font-size: 0.9em;"><strong>Nom :</strong> {}</p>
                <p style="font-size: 0.9em;"><strong>Contact :</strong> contact@exemple.com</p>
                <p style="font-size: 0.9em;"><strong>Téléphone :</strong> 01 23 45 67 89</p>
            </div>
            """.format(dossier['client']), unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h5>📊 État du dossier</h5>
                <p style="font-size: 0.9em;"><strong>Ouvert le :</strong> 15/01/2024</p>
                <p style="font-size: 0.9em;"><strong>Dernière action :</strong> 10/01/2024</p>
                <p style="font-size: 0.9em;"><strong>Prochaine échéance :</strong> 25/01/2024</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card" style="margin-top: 15px;">
            <h5>📝 Résumé de l'affaire</h5>
            <p style="font-size: 0.9em;">Cette affaire concerne un litige commercial entre notre client et la partie adverse 
            concernant l'exécution d'un contrat de prestation de services. Les principaux points de désaccord portent sur 
            les délais de livraison et la qualité des prestations fournies.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("##### 📁 Documents du dossier")
        
        docs = [
            ("Assignation initiale.pdf", "15/01/2024", "245 KB"),
            ("Conclusions en défense.docx", "20/01/2024", "189 KB"),
            ("Pièces justificatives.zip", "22/01/2024", "2.3 MB"),
        ]
        
        for doc, date, size in docs:
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.markdown(f"📄 **{doc}**")
            with col2:
                st.text(date)
            with col3:
                st.text(size)
            with col4:
                if st.button("⬇️", key=f"dl_{doc}"):
                    st.toast(f"Téléchargement de {doc}...")
    
    with tab3:
        st.markdown("##### ⏱️ Chronologie de l'affaire")
        
        events = [
            ("15/01/2024", "Ouverture du dossier", "🟢"),
            ("18/01/2024", "Réception assignation", "🔵"),
            ("20/01/2024", "Rédaction conclusions", "🟡"),
            ("25/01/2024", "Audience prévue", "🔴"),
        ]
        
        for date, event, color in events:
            st.markdown(f"""
            <div class="feature-card" style="margin-bottom: 8px; padding: 12px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 12px;">{color}</span>
                    <div>
                        <strong style="font-size: 0.9em;">{date}</strong> - <span style="font-size: 0.9em;">{event}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("##### 💬 Notes et commentaires")
        
        # Zone d'ajout de note
        new_note = st.text_area("Ajouter une note", placeholder="Tapez votre note ici...", height=80)
        if st.button("💾 Enregistrer", type="primary"):
            st.success("Note enregistrée !")
        
        # Notes existantes
        st.markdown("""
        <div class="feature-card" style="margin-top: 15px; padding: 15px;">
            <p style="font-size: 0.85em; color: var(--text-secondary); margin: 0;"><strong>10/01/2024 - 14:30</strong></p>
            <p style="font-size: 0.9em; margin: 5px 0;">Contact établi avec le client. Discussion sur la stratégie de défense.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab5:
        st.markdown("##### ⚖️ Procédures en cours")
        
        st.markdown("""
        <div class="feature-card">
            <h5 style="margin-top: 0;">🏛️ Tribunal de Grande Instance de Paris</h5>
            <p style="font-size: 0.9em;"><strong>N° RG :</strong> 24/00123</p>
            <p style="font-size: 0.9em;"><strong>Chambre :</strong> 2ème chambre civile</p>
            <p style="font-size: 0.9em;"><strong>Juge :</strong> M. Dupont</p>
            <p style="font-size: 0.9em;"><strong>Prochaine audience :</strong> 25/01/2024 à 14h00</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Bouton retour
    if st.button("⬅️ Retour au tableau de bord", use_container_width=True):
        st.session_state.current_view = 'dashboard'
        st.rerun()

# Page Dashboard
def show_dashboard():
    # Header sobre
    st.markdown("""
    <div class="main-header">
        <h1>Espace juridique intelligent</h1>
        <p>Optimisez votre pratique avec l'intelligence artificielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barre de recherche améliorée
    query, search_clicked = create_enhanced_search()
    
    # Traitement de la recherche
    if search_clicked and query:
        # Ne pas traiter ici si c'est une recherche @ car elle est déjà gérée dans create_enhanced_search
        if not query.strip().startswith("@"):
            process_search_query(query)
    
    # Métriques en cards
    st.markdown("#### 📊 Tableau de bord")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Documents", "156", "+12%")
    with col2:
        st.metric("Affaires", "23", "+2")
    with col3:
        st.metric("Temps économisé", "42h", "+15%")
    with col4:
        st.metric("Efficacité", "94%", "+3%")
    
    # Panneau d'aide pour la recherche
    with st.expander("💡 Comment utiliser la recherche intelligente ?"):
        st.markdown("""
        <div style="font-size: 0.9em;">
        <p><strong>La barre de recherche comprend vos questions en langage naturel !</strong></p>
        
        <p>📝 <strong>Exemples de questions que vous pouvez poser :</strong></p>
        <ul>
            <li>"Comment rédiger des conclusions ?"</li>
            <li>"Où trouver mes documents ?"</li>
            <li>"Comment ajouter un nouveau client ?"</li>
            <li>"Où est la jurisprudence ?"</li>
            <li>"Comment analyser un contrat ?"</li>
            <li>"Comment fonctionne l'application ?"</li>
        </ul>
        
        <p>📂 <strong>Pour rechercher un dossier :</strong></p>
        <ul>
            <li>Tapez @ suivi du nom du client : <code>@Martin</code></li>
            <li>Ou de la référence : <code>@2024-001</code></li>
            <li>Ou d'un mot-clé : <code>@divorce</code></li>
        </ul>
        
        <p>⌨️ <strong>Raccourcis :</strong></p>
        <ul>
            <li><code>Entrée</code> : Lancer la recherche</li>
            <li><code>Shift + Entrée</code> : Nouvelle ligne</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Sections principales
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🚀 Fonctionnalités principales")
    
    # Cards des fonctionnalités
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h5 style="color: var(--accent-color); margin-top: 0;">📝 Rédaction intelligente</h5>
            <p style="color: var(--text-secondary); font-size: 0.9em;">Générez tous vos documents juridiques</p>
            <div style="margin-top: 15px;">
                <span class="quick-action-chip">Conclusions</span>
                <span class="quick-action-chip">Assignations</span>
                <span class="quick-action-chip">Contrats</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h5 style="color: var(--accent-color); margin-top: 0;">🔍 Recherche juridique</h5>
            <p style="color: var(--text-secondary); font-size: 0.9em;">Accédez à toute la jurisprudence</p>
            <div style="margin-top: 15px;">
                <span class="quick-action-chip">Cassation</span>
                <span class="quick-action-chip">CE</span>
                <span class="quick-action-chip">Doctrine</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h5 style="color: var(--accent-color); margin-top: 0;">📊 Analyse de documents</h5>
            <p style="color: var(--text-secondary); font-size: 0.9em;">Analysez vos dossiers en profondeur</p>
            <div style="margin-top: 15px;">
                <span class="quick-action-chip">Risques</span>
                <span class="quick-action-chip">Timeline</span>
                <span class="quick-action-chip">Synthèse</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Page Rédaction
def show_redaction():
    st.title("📝 Rédaction juridique")
    
    # Type de document
    doc_type = st.selectbox(
        "Type de document",
        ["Conclusions", "Assignation", "Plaidoirie", "Contrat", "Consultation", "Autre"]
    )
    
    # Zone de saisie
    st.markdown("#### 📋 Informations sur l'affaire")
    
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Nom du client", placeholder="Ex: M. Martin")
        adversaire = st.text_input("Partie adverse", placeholder="Ex: SARL Dupont")
    
    with col2:
        juridiction = st.text_input("Juridiction", placeholder="Ex: TGI Paris")
        numero_rg = st.text_input("N° RG", placeholder="Ex: 23/12345")
    
    # Description de l'affaire
    st.markdown("#### 📝 Description")
    description = st.text_area(
        "Décrivez les faits et vos objectifs",
        height=150,
        placeholder="Décrivez en détail les faits de l'affaire, les points juridiques importants..."
    )
    
    # Bouton de génération
    if st.button("🚀 Générer le document", type="primary", use_container_width=True):
        with st.spinner("Génération en cours..."):
            time.sleep(2)
        st.success("✅ Document généré avec succès !")
        
        # Affichage du résultat simulé
        st.markdown("#### 📄 Document généré")
        st.markdown("""
        <div class="feature-card">
            <h5>CONCLUSIONS POUR {}</h5>
            <p style="font-size: 0.9em;"><strong>Pour :</strong> {}</p>
            <p style="font-size: 0.9em;"><strong>Contre :</strong> {}</p>
            <p style="font-size: 0.9em;"><strong>Devant :</strong> {}</p>
            <hr style="margin: 15px 0;">
            <p style="font-size: 0.9em;">PLAISE AU TRIBUNAL</p>
            <p style="font-size: 0.9em;">[Contenu généré par l'IA...]</p>
        </div>
        """.format(client_name or "[Client]", client_name or "[Client]", 
                   adversaire or "[Adversaire]", juridiction or "[Juridiction]"), 
        unsafe_allow_html=True)

# Page Recherche
def show_recherche():
    st.title("🔍 Recherche juridique")
    
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
        st.markdown("#### 📚 Résultats : 47 documents")
        
        for i in range(3):
            st.markdown(f"""
            <div class="feature-card" style="margin-bottom: 15px;">
                <h5 style="margin: 0;">🏛️ Cass. Civ. 1ère, {15-i} janvier 2024, n°23-1234{i}</h5>
                <p style="font-size: 0.85em; color: var(--text-secondary); margin: 8px 0;">
                    <strong>Mots-clés :</strong> Responsabilité contractuelle, Préjudice, Réparation
                </p>
                <p style="font-size: 0.9em;">La Cour de cassation rappelle que le débiteur n'est tenu que des 
                dommages et intérêts qui ont été prévus ou qu'on a pu prévoir...</p>
                <div style="margin-top: 12px;">
                    <span class="quick-action-chip">Lire</span>
                    <span class="quick-action-chip">Citer</span>
                    <span class="quick-action-chip">Analyser</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Page Analyse
def show_analyse():
    st.title("📊 Analyse de documents")
    
    # Upload de fichier
    uploaded_file = st.file_uploader(
        "Télécharger un document",
        type=['pdf', 'docx', 'txt'],
        help="Formats acceptés : PDF, DOCX, TXT"
    )
    
    if uploaded_file:
        st.success(f"✅ Fichier '{uploaded_file.name}' chargé")
        
        # Options d'analyse
        st.markdown("#### 🎯 Options d'analyse")
        
        col1, col2 = st.columns(2)
        with col1:
            analyses = st.multiselect(
                "Types d'analyse",
                ["Résumé", "Points clés", "Risques", "Jurisprudence", "Timeline", "Parties"]
            )
        
        with col2:
            format_output = st.radio(
                "Format",
                ["Détaillé", "Synthèse", "Points"]
            )
        
        if st.button("🚀 Analyser", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                time.sleep(2)
            
            st.markdown("#### 📈 Résultats")
            
            # Résultats simulés
            if "Résumé" in analyses:
                st.markdown("""
                <div class="feature-card">
                    <h5>📄 Résumé</h5>
                    <p style="font-size: 0.9em;">Ce document concerne un litige commercial entre deux sociétés 
                    concernant l'exécution d'un contrat de prestation de services...</p>
                </div>
                """, unsafe_allow_html=True)
            
            if "Risques" in analyses:
                st.markdown("""
                <div class="feature-card" style="margin-top: 12px;">
                    <h5>⚠️ Analyse des risques</h5>
                    <ul style="font-size: 0.9em;">
                        <li>🔴 <strong>Élevé :</strong> Prescription potentielle</li>
                        <li>🟡 <strong>Moyen :</strong> Preuve du préjudice</li>
                        <li>🟢 <strong>Faible :</strong> Compétence juridictionnelle</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

# Page Documents
def show_documents():
    st.title("📁 Gestion documentaire")
    
    # Barre de recherche et filtres
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("Rechercher", placeholder="Nom, client, type...")
    with col2:
        filter_type = st.selectbox("Type", ["Tous", "Conclusions", "Contrats", "Courriers"])
    with col3:
        sort_by = st.selectbox("Trier", ["Date ↓", "Date ↑", "Nom"])
    
    # Liste des documents
    st.markdown("#### 📄 Documents récents")
    
    documents = [
        {"nom": "Conclusions_Martin_vs_Dupont.pdf", "date": "2024-01-15", "client": "Martin", "taille": "245 KB"},
        {"nom": "Contrat_cession_parts.docx", "date": "2024-01-14", "client": "Tech Corp", "taille": "128 KB"},
        {"nom": "Assignation_TGI_Paris.pdf", "date": "2024-01-12", "client": "Leblanc", "taille": "189 KB"},
    ]
    
    for doc in documents:
        st.markdown(f"""
        <div class="feature-card" style="margin-bottom: 10px; padding: 12px 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="font-size: 0.95em;">📄 {doc['nom']}</strong>
                    <p style="margin: 2px 0; font-size: 0.85em; color: var(--text-secondary);">
                        {doc['client']} • {doc['date']} • {doc['taille']}
                    </p>
                </div>
                <button style="padding: 4px 12px; border: 1px solid var(--border-color); 
                              border-radius: 4px; background: white; cursor: pointer;">
                    ⬇️ Télécharger
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Page Clients
def show_clients():
    st.title("👥 Gestion des clients")
    
    # Ajout d'un nouveau client
    with st.expander("➕ Nouveau client"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom")
            email = st.text_input("Email")
        with col2:
            telephone = st.text_input("Téléphone")
            type_client = st.selectbox("Type", ["Particulier", "Entreprise", "Association"])
        
        if st.button("Enregistrer", type="primary"):
            st.success("✅ Client enregistré !")
    
    # Liste des clients
    st.markdown("#### 📋 Clients actifs")
    
    clients = [
        {"nom": "Martin Jean", "type": "Particulier", "affaires": 3, "dernier": "10/01/2024"},
        {"nom": "SARL Tech Corp", "type": "Entreprise", "affaires": 5, "dernier": "15/01/2024"},
        {"nom": "Association Envol", "type": "Association", "affaires": 2, "dernier": "08/01/2024"},
    ]
    
    for client in clients:
        st.markdown(f"""
        <div class="feature-card" style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h5 style="margin: 0; font-size: 1em;">{client['nom']}</h5>
                    <p style="margin: 3px 0; font-size: 0.85em; color: var(--text-secondary);">
                        {client['type']} • {client['affaires']} affaires • Dernier contact : {client['dernier']}
                    </p>
                </div>
                <div>
                    <span class="quick-action-chip">Détails</span>
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
        st.markdown("#### Informations personnelles")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Nom", value="Maître Dupont")
            st.text_input("Email", value="contact@cabinet.fr")
        with col2:
            st.text_input("Cabinet", value="Cabinet Dupont")
            st.text_input("Barreau", value="Paris")
        
        if st.button("Enregistrer", type="primary"):
            st.success("✅ Profil mis à jour !")
    
    with tab2:
        st.markdown("#### Sécurité")
        st.checkbox("Authentification à deux facteurs", value=True)
        st.checkbox("Notifications de connexion", value=True)
        
        if st.button("Changer le mot de passe"):
            st.info("Email envoyé")
    
    with tab3:
        st.markdown("#### Notifications")
        st.checkbox("Email", value=True)
        st.checkbox("Rappels", value=True)
        st.checkbox("Actualités juridiques", value=False)
    
    with tab4:
        st.markdown("#### Abonnement actuel")
        st.info("**Plan :** Premium")
        st.metric("Utilisation", "127 / 500", "25%")
        
        st.markdown("""
        <div class="feature-card">
            <h5>✨ Avantages Premium</h5>
            <ul style="font-size: 0.9em;">
                <li>500 requêtes IA/mois</li>
                <li>Accès illimité</li>
                <li>Support prioritaire</li>
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
    elif st.session_state.current_view == 'dossier_detail':
        show_dossier_detail()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #718096; font-size: 0.85em;'>⚖️ IA Juridique Pro • Assistant juridique intelligent</p>",
        unsafe_allow_html=True
    )

# Point d'entrée
if __name__ == "__main__":
    main()