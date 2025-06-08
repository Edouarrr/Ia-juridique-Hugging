# app.py
import streamlit as st

st.set_page_config(
    page_title="Assistant Pénal des Affaires IA", 
    page_icon="⚖️", 
    layout="wide"
)

import sys
import os
import traceback

from config.app_config import APP_CONFIG
from utils.helpers import initialize_session_state
from utils.styles import load_custom_css

def main():
    """Interface principale de l'application"""
    
    initialize_session_state()
    load_custom_css()
    
    # Initialisation Azure
    force_init_azure()
    
    # Titre principal
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1a237e; font-size: 3rem;'>⚖️ Assistant Pénal des Affaires IA</h1>
        <p style='color: #666; font-size: 1.2rem;'>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    # NAVIGATION UNIQUE
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        # Pages disponibles
        pages = {
            "🔍 Recherche": "recherche",
            "📁 Sélection": "selection", 
            "🤖 Analyse IA": "analyse",
            "📝 Rédaction": "redaction",
            "✉️ Courrier": "courrier",
            "📥 Import/Export": "import_export",
            "⚙️ Configuration": "configuration"
        }
        
        # Navigation avec boutons
        for page_name, page_key in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Page par défaut
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'recherche'
        
        st.markdown("---")
        st.markdown("### 📊 État du système")
        
        # Status Azure
        show_azure_status()
        
        # Métriques
        st.markdown("---")
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", nb_docs)
        with col2:
            st.metric("Pièces", nb_pieces)
    
    # ROUTAGE
    current_page = st.session_state.get('current_page', 'recherche')
    route_to_page(current_page)

def force_init_azure():
    """Initialise les gestionnaires Azure"""
    if 'azure_blob_manager' not in st.session_state:
        try:
            from managers.azure_blob_manager import AzureBlobManager
            st.session_state.azure_blob_manager = AzureBlobManager()
        except Exception as e:
            st.session_state.azure_blob_manager = None
    
    if 'azure_search_manager' not in st.session_state:
        try:
            from managers.azure_search_manager import AzureSearchManager
            st.session_state.azure_search_manager = AzureSearchManager()
        except Exception as e:
            st.session_state.azure_search_manager = None

def show_azure_status():
    """Affiche le statut Azure"""
    # Azure Blob
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
        st.success("✅ Azure Blob")
        containers = blob_manager.list_containers()
        if containers:
            st.caption(f"{len(containers)} containers")
    else:
        st.error("❌ Azure Blob")
    
    # Azure Search
    search_manager = st.session_state.get('azure_search_manager')
    if search_manager and hasattr(search_manager, 'search_client') and search_manager.search_client:
        st.success("✅ Azure Search")
    else:
        st.error("❌ Azure Search")

def route_to_page(page_key: str):
    """Route vers la bonne page"""
    
    try:
        if page_key == "recherche":
            # CHANGEMENT ICI : modules au lieu de pages
            from modules.recherche import show_page
            show_page()
            
        elif page_key == "configuration":
            show_configuration_page()
            
        else:
            # Pages placeholder
            page_info = {
                "selection": {"title": "Sélection de pièces", "icon": "📁"},
                "analyse": {"title": "Analyse IA", "icon": "🤖"},
                "redaction": {"title": "Rédaction assistée", "icon": "📝"},
                "courrier": {"title": "Rédaction de courrier", "icon": "✉️"},
                "import_export": {"title": "Import/Export", "icon": "📥"}
            }
            
            if page_key in page_info:
                info = page_info[page_key]
                st.header(f"{info['icon']} {info['title']}")
                st.success("✅ Module fonctionnel")
                
                # Fonctionnalités de démonstration
                if page_key == "selection":
                    show_selection_demo()
                elif page_key == "analyse":
                    show_analyse_demo()
                elif page_key == "redaction":
                    show_redaction_demo()
                elif page_key == "courrier":
                    show_courrier_demo()
                elif page_key == "import_export":
                    show_import_demo()
                
            else:
                st.error(f"❌ Page inconnue: {page_key}")
                
    except Exception as e:
        st.error(f"❌ Erreur page '{page_key}': {str(e)}")
        st.code(traceback.format_exc())

def show_selection_demo():
    """Démo de sélection de pièces"""
    st.info("📋 Interface de sélection de pièces")
    
    # Simuler des documents
    documents_demo = [
        {"nom": "Contrat_société.pdf", "type": "Contrat", "taille": "156 KB"},
        {"nom": "Procès_verbal_AG.docx", "type": "PV", "taille": "89 KB"},
        {"nom": "Relevé_bancaire.pdf", "type": "Comptabilité", "taille": "234 KB"}
    ]
    
    st.markdown("**Documents disponibles :**")
    for doc in documents_demo:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.text(f"📄 {doc['nom']}")
        with col2:
            st.caption(doc['taille'])
        with col3:
            if st.button("➕", key=f"add_{doc['nom']}"):
                st.success(f"✅ {doc['nom']} ajouté")

def show_analyse_demo():
    """Démo d'analyse IA"""
    st.info("🤖 Interface d'analyse par IA")
    
    analyse_types = [
        "🎯 Analyse infractions économiques",
        "🏢 Responsabilité personne morale", 
        "🛡️ Moyens de défense",
        "💰 Enjeux financiers"
    ]
    
    selected_analyses = st.multiselect(
        "Types d'analyse",
        analyse_types,
        default=analyse_types[:2]
    )
    
    if st.button("🚀 Lancer l'analyse", type="primary"):
        with st.spinner("Analyse en cours..."):
            st.success("✅ Analyse terminée !")
            
            for analyse in selected_analyses:
                with st.expander(analyse):
                    st.write("Résultat de l'analyse simulée...")

def show_redaction_demo():
    """Démo de rédaction assistée"""
    st.info("📝 Interface de rédaction assistée")
    
    type_acte = st.selectbox(
        "Type d'acte",
        ["Conclusions en défense", "Plainte", "Mémoire", "Courrier"]
    )
    
    client = st.text_input("Client", "Société XYZ")
    
    if st.button("✍️ Générer l'acte", type="primary"):
        with st.spinner("Génération en cours..."):
            st.success("✅ Acte généré !")
            st.text_area(
                "Acte généré",
                f"Monsieur le Président,\n\nJ'ai l'honneur de vous présenter les conclusions en défense pour {client}...",
                height=300
            )

def show_courrier_demo():
    """Démo de rédaction de courrier"""
    st.info("✉️ Interface de rédaction de courrier")
    
    destinataire = st.text_input("Destinataire", "Maître Martin")
    objet = st.text_input("Objet", "Affaire Société XYZ")
    
    if st.button("📧 Générer le courrier", type="primary"):
        with st.spinner("Génération en cours..."):
            st.success("✅ Courrier généré !")
            st.text_area(
                "Courrier généré",
                f"Cher {destinataire},\n\nConcernant {objet}, j'ai l'honneur de vous informer...",
                height=300
            )

def show_import_demo():
    """Démo d'import/export"""
    st.info("📥 Interface d'import/export")
    
    uploaded_file = st.file_uploader(
        "Importer un document",
        type=['pdf', 'docx', 'txt']
    )
    
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name} importé avec succès")
        st.write(f"Taille: {uploaded_file.size} bytes")

def show_configuration_page():
    """Page de configuration"""
    st.header("⚙️ Configuration")
    
    tabs = st.tabs(["🔑 Variables", "🔧 Azure", "🤖 IA"])
    
    with tabs[0]:
        st.subheader("Variables d'environnement")
        vars_to_check = [
            ("AZURE_STORAGE_CONNECTION_STRING", "Azure Blob Storage"),
            ("AZURE_SEARCH_ENDPOINT", "Azure Search URL"),
            ("AZURE_SEARCH_KEY", "Azure Search Key")
        ]
        
        for var, desc in vars_to_check:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(desc)
            with col2:
                if os.getenv(var):
                    st.success("✅")
                else:
                    st.error("❌")
    
    with tabs[1]:
        st.subheader("État Azure")
        
        blob_manager = st.session_state.get('azure_blob_manager')
        if blob_manager and blob_manager.is_connected():
            st.success("✅ Azure Blob connecté")
            containers = blob_manager.list_containers()
            st.write(f"**Containers:** {containers}")
        else:
            st.error("❌ Azure Blob non connecté")
        
        search_manager = st.session_state.get('azure_search_manager')
        if search_manager and search_manager.search_client:
            st.success("✅ Azure Search connecté")
        else:
            st.error("❌ Azure Search non connecté")
    
    with tabs[2]:
        st.subheader("Intelligence Artificielle")
        try:
            from managers.multi_llm_manager import MultiLLMManager
            llm_manager = MultiLLMManager()
            providers = llm_manager.get_available_providers()
            
            st.write(f"**Providers disponibles:** {len(providers)}")
            for provider in providers:
                st.success(f"✅ {provider}")
        except:
            st.error("❌ LLM Manager non disponible")

if __name__ == "__main__":
    main()