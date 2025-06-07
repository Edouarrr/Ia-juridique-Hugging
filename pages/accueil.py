# pages/accueil.py
"""Page d'accueil de l'application"""

import streamlit as st
from datetime import datetime

# Import sécurisé avec valeurs par défaut
try:
    from config.app_config import APP_TITLE, APP_VERSION, APP_ICON, TYPES_INFRACTIONS
except ImportError:
    APP_TITLE = "Assistant Pénal des Affaires IA"
    APP_VERSION = "3.0.0"
    APP_ICON = "⚖️"
    TYPES_INFRACTIONS = [
        "Abus de biens sociaux",
        "Abus de confiance",
        "Corruption",
        "Fraude fiscale",
        "Blanchiment"
    ]

try:
    from utils.styles import load_custom_css, format_metric_card
except ImportError:
    def load_custom_css():
        pass
    def format_metric_card(title, value, color="primary"):
        return f"<div style='background-color: #f5f5f5; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'><h4>{title}</h4><p>{value}</p></div>"


def show():
    """Affiche la page d'accueil"""
    # Charger les styles CSS si disponibles
    try:
        load_custom_css()
    except:
        pass
    
    # Titre principal
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.markdown("Intelligence artificielle au service du droit pénal économique")
    
    # Message de bienvenue
    st.markdown("## 👋 Bienvenue dans l'Assistant Pénal des Affaires IA")
    st.info("Cette plateforme utilise l'intelligence artificielle pour vous accompagner dans vos analyses juridiques en droit pénal des affaires.")
    
    # Section des fonctionnalités principales
    st.markdown("## 🚀 Fonctionnalités principales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background-color: #f5f5f5; padding: 1.5rem; border-radius: 10px; height: 200px;'>
            <h3 style='color: #1a237e;'>🔍 Recherche intelligente</h3>
            <p>Explorez vos documents SharePoint et recherchez dans la jurisprudence</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Accéder à la recherche", key="btn_recherche", use_container_width=True):
            st.info("👉 Utilisez le menu de navigation à gauche pour accéder à la recherche")
    
    with col2:
        st.markdown("""
        <div style='background-color: #f5f5f5; padding: 1.5rem; border-radius: 10px; height: 200px;'>
            <h3 style='color: #4caf50;'>📋 Analyse juridique</h3>
            <p>Analysez vos documents avec l'aide de l'IA et générez des insights</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Lancer une analyse", key="btn_analyse", use_container_width=True):
            st.info("👉 Utilisez le menu de navigation à gauche pour accéder à l'analyse")
    
    with col3:
        st.markdown("""
        <div style='background-color: #f5f5f5; padding: 1.5rem; border-radius: 10px; height: 200px;'>
            <h3 style='color: #2196f3;'>💬 Assistant interactif</h3>
            <p>Posez vos questions juridiques et obtenez des réponses instantanées</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Démarrer l'assistant", key="btn_assistant", use_container_width=True):
            st.info("👉 Utilisez le menu de navigation à gauche pour accéder à l'assistant")
    
    # Statistiques et métriques
    st.markdown("---")
    st.markdown("## 📊 Tableau de bord")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nb_docs = len(st.session_state.get('azure_documents', {}))
        st.metric(
            "Documents chargés",
            nb_docs,
            delta=f"+{nb_docs}" if nb_docs > 0 else None
        )
    
    with col2:
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        st.metric(
            "Pièces sélectionnées",
            nb_pieces,
            delta=f"+{nb_pieces}" if nb_pieces > 0 else None
        )
    
    with col3:
        nb_analyses = st.session_state.get('analyses_count', 0)
        st.metric(
            "Analyses effectuées",
            nb_analyses
        )
    
    with col4:
        nb_styles = len(st.session_state.get('learned_styles', {}))
        st.metric(
            "Styles appris",
            nb_styles
        )
    
    # Section d'aide rapide
    st.markdown("---")
    st.markdown("## 💡 Aide rapide")
    
    # Comment démarrer
    with st.expander("🎯 Comment démarrer ?", expanded=True):
        st.markdown("""
        ### Étapes pour bien commencer :
        
        1. **📂 Recherchez vos documents**
           - Utilisez la fonction de recherche pour explorer vos documents SharePoint
           - Naviguez dans les dossiers et sélectionnez les fichiers pertinents
        
        2. **📌 Sélectionnez les pièces pertinentes**
           - Organisez vos documents par catégorie
           - Préparez votre dossier pour l'analyse
        
        3. **🤖 Lancez une analyse**
           - Utilisez l'IA pour analyser vos documents
           - Obtenez des insights juridiques pertinents
        
        4. **📝 Générez des documents**
           - Créez des plaintes, conclusions ou courriers
           - Utilisez les modèles adaptés à votre besoin
        
        5. **💬 Consultez l'assistant**
           - Posez vos questions juridiques spécifiques
           - Obtenez des réponses personnalisées
        """)
    
    # Types d'infractions
    with st.expander("📚 Types d'infractions supportées"):
        st.markdown("### Infractions prises en charge par l'application :")
        
        # Afficher les infractions en colonnes
        cols = st.columns(3)
        for i, infraction in enumerate(TYPES_INFRACTIONS[:15]):  # Limiter à 15 pour éviter les erreurs
            with cols[i % 3]:
                st.write(f"• {infraction}")
        
        if len(TYPES_INFRACTIONS) > 15:
            st.info(f"... et {len(TYPES_INFRACTIONS) - 15} autres infractions")
    
    # Configuration requise
    with st.expander("🔧 Configuration requise"):
        st.markdown("""
        ### Services Azure nécessaires :
        - ✅ **Azure Blob Storage** - Pour accéder à vos documents SharePoint
        - ✅ **Azure Search** - Pour la recherche vectorielle avancée
        - ✅ **Azure OpenAI** - Pour les embeddings et l'analyse
        
        ### IA supportées :
        - 🤖 **Claude** (Anthropic) - Pour les analyses juridiques complexes
        - 🤖 **GPT-4** (OpenAI/Azure) - Pour la génération de contenu
        - 🤖 **Gemini** (Google) - Pour les recherches contextuelles
        - 🤖 **Perplexity** - Pour les recherches web avancées
        - 🤖 **Mistral** - Pour les tâches spécialisées
        
        ### Configuration minimale :
        - Connexion internet stable
        - Navigateur moderne (Chrome, Firefox, Edge)
        - Accès aux services Azure configurés
        """)
    
    # Section actualités
    st.markdown("---")
    st.markdown("## 📰 Actualités juridiques")
    
    # Colonnes pour les actualités
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #1a237e;'>
            <h4 style='margin: 0; color: #1a237e;'>Nouvelle jurisprudence ABS</h4>
            <p style='margin: 0.5rem 0; color: #666; font-size: 0.9rem;'>15 juin 2025</p>
            <p style='margin: 0;'>La Cour de cassation précise les conditions de caractérisation de l'abus de biens sociaux en cas de confusion de patrimoine...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #4caf50;'>
            <h4 style='margin: 0; color: #4caf50;'>Guide conformité AFA</h4>
            <p style='margin: 0.5rem 0; color: #666; font-size: 0.9rem;'>10 juin 2025</p>
            <p style='margin: 0;'>L'Agence française anticorruption publie ses nouvelles recommandations pour les programmes de conformité...</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    
    # Informations de version
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Version** : {APP_VERSION}")
    
    with col2:
        st.markdown(f"**Dernière mise à jour** : {datetime.now().strftime('%d/%m/%Y')}")
    
    with col3:
        st.markdown("**Support** : contact@assistant-penal.ai")
    
    # Copyright
    st.markdown(
        f"""
        <div style='text-align: center; color: #666; padding: 1rem; margin-top: 2rem;'>
            <p>© 2025 {APP_TITLE} - Tous droits réservés</p>
            <p style='font-size: 0.9rem;'>Développé avec ❤️ pour les professionnels du droit</p>
        </div>
        """, 
        unsafe_allow_html=True
    )