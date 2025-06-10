"""Application principale avec gestion Azure et interface de recherche améliorée"""

import streamlit as st
from datetime import datetime
import asyncio
from typing import Dict, List, Optional
import re
import sys
import os
import traceback

print("=== DÉMARRAGE APPLICATION ===")

# Configuration de la page
st.set_page_config(
    page_title="Assistant Pénal des Affaires IA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import corrigé - utiliser app_config au lieu de APP_CONFIG
from config.app_config import app_config, api_config
from utils.helpers import initialize_session_state
from utils.styles import load_custom_css

# Import des services - CORRECTION: managers au lieu de services
from managers.universal_search_service import UniversalSearchService

# Styles CSS personnalisés fusionnés
st.markdown("""
<style>
    /* Styles de base */
    .main-title {
        text-align: center;
        padding: 2rem 0;
    }
    
    .main-title h1 {
        color: #1a237e;
        font-size: 3rem;
    }
    
    .main-title p {
        color: #666;
        font-size: 1.2rem;
    }
    
    /* Styles pour la barre de recherche */
    .search-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    /* Style pour les résultats */
    .result-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .result-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
    
    /* Style pour les tags */
    .tag {
        display: inline-block;
        padding: 4px 8px;
        margin: 2px;
        background-color: #e1ecf4;
        border-radius: 3px;
        font-size: 0.85em;
        color: #39739d;
    }
    
    /* Style pour la référence @ */
    .reference-tag {
        background-color: #ffd93d;
        color: #6c4a00;
        font-weight: bold;
    }
    
    /* Indicateur de recherche */
    .search-indicator {
        text-align: center;
        color: #666;
        font-style: italic;
        margin: 20px 0;
    }
    
    /* Bouton de recherche amélioré */
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1557a0;
        transform: translateY(-2px);
    }
    
    /* Styles pour les métriques Azure */
    .azure-status {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    
    .azure-connected {
        background-color: #d4edda;
        color: #155724;
    }
    
    .azure-disconnected {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* Style pour les highlights */
    mark {
        background-color: #ffd93d;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Nouveau style pour l'indicateur de version */
    .version-indicator {
        background-color: #ffd93d;
        color: #6c4a00;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation du service de recherche
@st.cache_resource
def get_search_service():
    """Initialise et retourne le service de recherche"""
    return UniversalSearchService()

def init_azure_managers():
    """Initialise les gestionnaires Azure avec logs détaillés"""
    
    print("=== INITIALISATION AZURE ===")
    
    # Azure Blob Manager
    if 'azure_blob_manager' not in st.session_state or st.session_state.azure_blob_manager is None:
        print("Initialisation Azure Blob Manager...")
        try:
            from managers.azure_blob_manager import AzureBlobManager
            
            print("Import AzureBlobManager réussi")
            manager = AzureBlobManager()
            print(f"AzureBlobManager créé: {manager}")
            
            st.session_state.azure_blob_manager = manager
            
            if hasattr(manager, 'is_connected') and manager.is_connected():
                print("✅ Azure Blob connecté avec succès")
                containers = manager.list_containers()
                print(f"Containers trouvés: {containers}")
            else:
                print("❌ Azure Blob non connecté")
                if hasattr(manager, 'get_connection_error'):
                    error = manager.get_connection_error()
                    print(f"Erreur: {error}")
                    
        except Exception as e:
            print(f"❌ Erreur fatale Azure Blob: {e}")
            print(traceback.format_exc())
            st.session_state.azure_blob_manager = None
    else:
        print("Azure Blob Manager déjà initialisé")
    
    # Azure Search Manager  
    if 'azure_search_manager' not in st.session_state or st.session_state.azure_search_manager is None:
        print("Initialisation Azure Search Manager...")
        try:
            from managers.azure_search_manager import AzureSearchManager
            
            print("Import AzureSearchManager réussi")
            manager = AzureSearchManager()
            print(f"AzureSearchManager créé: {manager}")
            
            st.session_state.azure_search_manager = manager
            
            if hasattr(manager, 'search_client') and manager.search_client:
                print("✅ Azure Search connecté avec succès")
            else:
                print("❌ Azure Search non connecté")
                if hasattr(manager, 'get_connection_error'):
                    error = manager.get_connection_error()
                    print(f"Erreur: {error}")
                    
        except Exception as e:
            print(f"❌ Erreur fatale Azure Search: {e}")
            print(traceback.format_exc())
            st.session_state.azure_search_manager = None
    else:
        print("Azure Search Manager déjà initialisé")

def reinit_azure():
    """Force la réinitialisation d'Azure"""
    print("=== RÉINITIALISATION AZURE FORCÉE ===")
    
    # Supprimer les managers existants
    if 'azure_blob_manager' in st.session_state:
        del st.session_state.azure_blob_manager
    if 'azure_search_manager' in st.session_state:
        del st.session_state.azure_search_manager
    
    # Réinitialiser
    init_azure_managers()
    
    st.rerun()

def show_azure_status_detailed():
    """Affichage détaillé du statut Azure avec diagnostics"""
    
    # Test des variables d'environnement
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    search_key = os.getenv('AZURE_SEARCH_KEY')
    
    # Azure Blob
    st.markdown("**Azure Blob Storage**")
    blob_manager = st.session_state.get('azure_blob_manager')
    
    if not conn_str:
        st.error("❌ Connection String manquante")
    elif not blob_manager:
        st.error("❌ Manager non initialisé")
    elif hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
        st.success("✅ Connecté")
        containers = blob_manager.list_containers()
        if containers:
            st.caption(f"{len(containers)} containers")
        else:
            st.caption("0 containers")
    else:
        st.error("❌ Non connecté")
        if hasattr(blob_manager, 'get_connection_error'):
            error = blob_manager.get_connection_error()
            st.caption(error[:40] + "..." if error and len(error) > 40 else error or "Erreur inconnue")
    
    # Azure Search
    st.markdown("**Azure Search**")
    search_manager = st.session_state.get('azure_search_manager')
    
    if not search_endpoint or not search_key:
        st.error("❌ Endpoint/Key manquant")
    elif not search_manager:
        st.error("❌ Manager non initialisé")
    elif hasattr(search_manager, 'search_client') and search_manager.search_client:
        st.success("✅ Connecté")
        st.caption("Index: search-rag-juridique")  # MODIFICATION ICI : nouvel index
    else:
        st.error("❌ Non connecté")
        if hasattr(search_manager, 'get_connection_error'):
            error = search_manager.get_connection_error()
            st.caption(error[:40] + "..." if error and len(error) > 40 else error or "Erreur inconnue")

def show_configuration_modal():
    """Affiche la configuration dans un modal"""
    with st.container():
        st.markdown("---")
        st.header("⚙️ Configuration")
        
        tabs = st.tabs(["🔑 Variables", "🔧 Azure", "🧪 Tests"])
        
        with tabs[0]:
            st.subheader("Variables d'environnement")
            
            vars_to_check = [
                ("AZURE_STORAGE_CONNECTION_STRING", "Azure Blob Storage"),
                ("AZURE_SEARCH_ENDPOINT", "Azure Search URL"),
                ("AZURE_SEARCH_KEY", "Azure Search Key"),
                ("ANTHROPIC_API_KEY", "Claude API"),
                ("OPENAI_API_KEY", "OpenAI API"),
                ("GOOGLE_API_KEY", "Google Gemini API")
            ]
            
            for var, desc in vars_to_check:
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    st.text(desc)
                with col2:
                    if os.getenv(var):
                        st.success("✅")
                    else:
                        st.error("❌")
                with col3:
                    if os.getenv(var):
                        value = os.getenv(var)
                        st.caption(f"{value[:20]}...")
        
        with tabs[1]:
            st.subheader("Diagnostics Azure détaillés")
            
            # Azure Blob
            with st.expander("🗄️ Azure Blob Storage", expanded=True):
                blob_manager = st.session_state.get('azure_blob_manager')
                
                conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                st.write(f"**Connection String:** {'✅ Présente' if conn_str else '❌ Manquante'}")
                
                if blob_manager:
                    st.write(f"**Manager:** ✅ Initialisé")
                    if hasattr(blob_manager, 'is_connected') and blob_manager.is_connected():
                        st.success("✅ Connexion active")
                        containers = blob_manager.list_containers()
                        st.write(f"**Containers:** {len(containers)}")
                        for container in containers[:5]:
                            st.text(f"• {container}")
                    else:
                        st.error("❌ Connexion échouée")
                        if hasattr(blob_manager, 'get_connection_error'):
                            error = blob_manager.get_connection_error()
                            st.error(f"**Erreur:** {error}")
                else:
                    st.error("❌ Manager non initialisé")
            
            # Azure Search
            with st.expander("🔍 Azure Search", expanded=True):
                search_manager = st.session_state.get('azure_search_manager')
                
                endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
                key = os.getenv('AZURE_SEARCH_KEY')
                st.write(f"**Endpoint:** {'✅ Présent' if endpoint else '❌ Manquant'}")
                st.write(f"**Key:** {'✅ Présente' if key else '❌ Manquante'}")
                
                if search_manager:
                    st.write(f"**Manager:** ✅ Initialisé")
                    if hasattr(search_manager, 'search_client') and search_manager.search_client:
                        st.success("✅ Connexion active")
                        st.write(f"**Index:** {getattr(search_manager, 'index_name', 'search-rag-juridique')}")  # MODIFICATION ICI : nouvel index
                    else:
                        st.error("❌ Connexion échouée")
                        if hasattr(search_manager, 'get_connection_error'):
                            error = search_manager.get_connection_error()
                            st.error(f"**Erreur:** {error}")
                else:
                    st.error("❌ Manager non initialisé")
        
        with tabs[2]:
            st.subheader("Tests de connexion")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🧪 Tester Azure Blob", key="test_blob", use_container_width=True):
                    test_azure_blob()
            
            with col2:
                if st.button("🧪 Tester Azure Search", key="test_search", use_container_width=True):
                    test_azure_search()
            
            with col3:
                if st.button("🧪 Tester tout", key="test_all", use_container_width=True):
                    test_azure_blob()
                    test_azure_search()
            
            # Affichage des informations de configuration
            if app_config:
                st.markdown("---")
                st.subheader("Configuration actuelle")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Version app:** {app_config.version}")
                    st.write(f"**Debug mode:** {app_config.debug}")
                    st.write(f"**Max file size:** {app_config.max_file_size_mb} MB")
                    st.write(f"**Max files:** {app_config.max_files_per_upload}")
                
                with col2:
                    st.write(f"**Azure Storage:** {'✅' if app_config.enable_azure_storage else '❌'}")
                    st.write(f"**Azure Search:** {'✅' if app_config.enable_azure_search else '❌'}")
                    st.write(f"**Multi-LLM:** {'✅' if app_config.enable_multi_llm else '❌'}")
                    st.write(f"**Email:** {'✅' if app_config.enable_email else '❌'}")
        
        if st.button("❌ Fermer", key="close_config"):
            st.session_state.show_config_modal = False
            st.rerun()

def test_azure_blob():
    """Test de connexion Azure Blob"""
    with st.spinner("Test Azure Blob..."):
        try:
            from managers.azure_blob_manager import AzureBlobManager
            test_manager = AzureBlobManager()
            
            if test_manager.is_connected():
                containers = test_manager.list_containers()
                st.success(f"✅ Azure Blob OK - {len(containers)} containers")
            else:
                error = test_manager.get_connection_error()
                st.error(f"❌ Azure Blob KO: {error}")
        except Exception as e:
            st.error(f"❌ Erreur test Azure Blob: {e}")

def test_azure_search():
    """Test de connexion Azure Search"""
    with st.spinner("Test Azure Search..."):
        try:
            from managers.azure_search_manager import AzureSearchManager
            test_manager = AzureSearchManager()
            
            if test_manager.search_client:
                st.success("✅ Azure Search OK")
            else:
                error = test_manager.get_connection_error()
                st.error(f"❌ Azure Search KO: {error}")
        except Exception as e:
            st.error(f"❌ Erreur test Azure Search: {e}")

# Fonction pour afficher les suggestions
def show_search_suggestions(query: str):
    """Affiche des suggestions basées sur la requête"""
    suggestions = []
    
    if query:
        # Suggestions de références @
        if '@' in query and not re.search(r'@\w+', query):
            suggestions.extend([
                "@VINCI2024", "@SOGEPROM", "@PERINET", "@ABS001"
            ])
        
        # Suggestions de types de documents
        if len(query) > 2:
            doc_types = ["conclusions", "plainte", "assignation", "courrier", "expertise"]
            for doc_type in doc_types:
                if doc_type.startswith(query.lower()):
                    suggestions.append(doc_type)
        
        # Suggestions d'infractions
        if "infraction" in query.lower() or "abus" in query.lower():
            suggestions.extend([
                "abus de biens sociaux", "corruption", "escroquerie"
            ])
    
    if suggestions:
        st.caption("💡 Suggestions:")
        cols = st.columns(min(len(suggestions), 4))
        for idx, suggestion in enumerate(suggestions[:4]):
            with cols[idx]:
                if st.button(suggestion, key=f"sugg_{idx}"):
                    # Au lieu de modifier search_input, on stocke la suggestion
                    st.session_state.selected_suggestion = query + " " + suggestion
                    st.rerun()

# Fonction principale de recherche
async def perform_search(query: str, filters: Optional[Dict] = None):
    """Effectue la recherche et affiche les résultats"""
    search_service = get_search_service()
    
    # Indicateur de recherche en cours
    with st.spinner(f"🔍 Recherche en cours pour : **{query}**"):
        results = await search_service.search(query, filters)
    
    return results

# Fonction pour afficher un résultat améliorée
def display_result_enhanced(doc, index: int):
    """Affiche un résultat de recherche avec highlights"""
    with st.container():
        col1, col2 = st.columns([10, 2])
        
        with col1:
            # Titre avec numéro et score
            score_badge = ""
            if doc.metadata.get('score', 0) >= 20:
                score_badge = "🔥"  # Haute pertinence
            elif doc.metadata.get('score', 0) >= 10:
                score_badge = "⭐"  # Pertinence moyenne
            
            st.markdown(f"### {index}. {doc.title} {score_badge}")
            
            # Afficher les métadonnées
            metadata_cols = st.columns(4)
            with metadata_cols[0]:
                st.caption(f"📄 Source: {doc.source}")
            with metadata_cols[1]:
                st.caption(f"🆔 ID: {doc.id[:8]}...")
            with metadata_cols[2]:
                if doc.metadata.get('score'):
                    st.caption(f"⭐ Score: {doc.metadata['score']:.2f}")
            with metadata_cols[3]:
                if doc.metadata.get('type'):
                    st.caption(f"📁 Type: {doc.metadata['type']}")
            
            # Afficher les highlights s'ils existent
            if hasattr(doc, 'highlights') and doc.highlights:
                st.markdown("**Extraits pertinents:**")
                for highlight in doc.highlights[:3]:
                    st.markdown(f"> *...{highlight}...*")
            else:
                # Sinon, afficher un extrait du contenu
                content_preview = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
                st.markdown(f"<div class='result-card'>{content_preview}</div>", unsafe_allow_html=True)
            
            # Afficher la date si disponible
            if doc.metadata.get('date'):
                st.caption(f"📅 Date: {doc.metadata['date']}")
        
        with col2:
            # Boutons d'action
            if st.button("📖 Voir détails", key=f"view_{index}"):
                st.session_state.selected_document = doc
                st.session_state.show_document_modal = True
            
            if st.button("📥 Télécharger", key=f"download_{index}"):
                # Implémenter le téléchargement
                pass
            
            if st.button("🔗 Partager", key=f"share_{index}"):
                # Implémenter le partage
                pass

def display_search_facets(facets: Dict[str, Dict[str, int]]):
    """Affiche les facettes de recherche pour filtrage dynamique"""
    if not facets:
        return
    
    st.markdown("### 📊 Affiner la recherche")
    
    cols = st.columns(3)
    
    # Facette Sources
    with cols[0]:
        if facets.get('sources'):
            st.markdown("**Sources**")
            for source, count in sorted(facets['sources'].items(), key=lambda x: x[1], reverse=True)[:5]:
                if st.checkbox(f"{source} ({count})", key=f"facet_source_{source}"):
                    # Ajouter au filtre
                    if 'active_filters' not in st.session_state:
                        st.session_state.active_filters = {}
                    st.session_state.active_filters['source'] = source
    
    # Facette Types
    with cols[1]:
        if facets.get('types'):
            st.markdown("**Types de documents**")
            for doc_type, count in sorted(facets['types'].items(), key=lambda x: x[1], reverse=True)[:5]:
                type_display = doc_type.upper() if doc_type != 'unknown' else 'Non classé'
                if st.checkbox(f"{type_display} ({count})", key=f"facet_type_{doc_type}"):
                    # Ajouter au filtre
                    if 'active_filters' not in st.session_state:
                        st.session_state.active_filters = {}
                    st.session_state.active_filters['type'] = doc_type
    
    # Facette Scores
    with cols[2]:
        if facets.get('scores'):
            st.markdown("**Pertinence**")
            scores = facets['scores']
            if scores.get('high', 0) > 0:
                if st.checkbox(f"🔥 Très pertinent ({scores['high']})", key="facet_score_high"):
                    st.session_state.filter_high_score = True
            if scores.get('medium', 0) > 0:
                if st.checkbox(f"⭐ Pertinent ({scores['medium']})", key="facet_score_medium"):
                    st.session_state.filter_medium_score = True
            if scores.get('low', 0) > 0:
                if st.checkbox(f"📄 Peu pertinent ({scores['low']})", key="facet_score_low"):
                    st.session_state.filter_low_score = True

def display_search_suggestions(suggestions: List[str]):
    """Affiche les suggestions de recherche alternative"""
    if not suggestions:
        return
    
    st.markdown("### 💡 Essayez aussi")
    
    cols = st.columns(len(suggestions))
    for idx, suggestion in enumerate(suggestions):
        with cols[idx]:
            if st.button(f"🔍 {suggestion}", key=f"suggestion_{idx}", use_container_width=True):
                # Stocker la suggestion pour la prochaine recherche
                st.session_state.pending_search = suggestion
                st.rerun()

def show_document_modal():
    """Affiche le modal de détail d'un document"""
    if st.session_state.get('show_document_modal') and st.session_state.get('selected_document'):
        doc = st.session_state.selected_document
        
        with st.container():
            st.markdown("---")
            st.markdown(f"## 📄 {doc.title}")
            
            # Métadonnées
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Source:** {doc.source}")
            with col2:
                st.write(f"**Type:** {doc.metadata.get('type', 'Document')}")
            with col3:
                if doc.metadata.get('date'):
                    st.write(f"**Date:** {doc.metadata['date']}")
            
            # Contenu complet
            st.markdown("### Contenu")
            
            # Si highlights disponibles, les mettre en évidence
            if hasattr(doc, 'highlights') and doc.highlights:
                content_with_highlights = doc.content
                for highlight in doc.highlights:
                    # Mettre en surbrillance les passages
                    content_with_highlights = content_with_highlights.replace(
                        highlight, 
                        f"<mark style='background-color: #ffd93d;'>{highlight}</mark>"
                    )
                st.markdown(content_with_highlights, unsafe_allow_html=True)
            else:
                st.text_area("", doc.content, height=400, disabled=True)
            
            # Actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📥 Télécharger", key="modal_download"):
                    # Implémenter le téléchargement
                    pass
            with col2:
                if st.button("📧 Envoyer par email", key="modal_email"):
                    # Implémenter l'envoi
                    pass
            with col3:
                if st.button("❌ Fermer", key="modal_close"):
                    st.session_state.show_document_modal = False
                    st.session_state.selected_document = None
                    st.rerun()

# ====== NOUVELLE FONCTION POUR LA RECHERCHE UNIFIÉE ======
def show_simplified_search():
    """Affiche l'interface de recherche unifiée"""
    try:
        from modules import recherche  # Module unifié
        
        # Indicateur de version
        st.markdown('<div class="version-indicator">✨ VERSION UNIFIÉE</div>', unsafe_allow_html=True)
        
        # Afficher l'interface unifiée
        recherche.show_page()
        
    except ImportError as e:
        st.error("❌ Module recherche.py non trouvé !")
        st.info("Assurez-vous d'avoir créé le fichier modules/recherche.py avec le code unifié")
        with st.expander("Détails de l'erreur"):
            st.code(str(e))
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de la recherche unifiée: {str(e)}")
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())

# ====== FONCTION PRINCIPALE MODIFIÉE ======
def main():
    """Interface principale de l'application"""
    
    print("=== DÉBUT MAIN ===")
    
    # Initialisation
    initialize_session_state()
    load_custom_css()
    
    # FORCER l'initialisation Azure AU DÉBUT
    init_azure_managers()
    
    # Titre principal
    st.markdown("""
    <div class='main-title'>
        <h1>⚖️ Assistant Pénal des Affaires IA</h1>
        <p>Intelligence artificielle au service du droit pénal économique</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ====== NOUVELLE SECTION : CHOIX DE VERSION ======
    # Barre latérale avec choix de version en premier
    with st.sidebar:
        st.header("🔧 Version de l'interface")
        
        # Option de basculement entre versions
        use_simplified = st.toggle(
            "✨ Utiliser la version unifiée",
            value=st.session_state.get('use_simplified_version', False),
            help="Version optimisée avec toutes les fonctionnalités et sans redondances"
        )
        
        # Sauvegarder le choix
        st.session_state.use_simplified_version = use_simplified
        
        if use_simplified:
            st.info("✨ Version unifiée active")
            st.caption("Combine le meilleur des deux versions : interface simplifiée + fonctionnalités avancées")
        else:
            st.info("📋 Version classique active")
            st.caption("Version originale avec interface de recherche traditionnelle")
        
        st.markdown("---")
        
        # État du système Azure
        st.header("📊 État du système")
        show_azure_status_detailed()
        
        # Métriques
        st.markdown("---")
        nb_docs = len(st.session_state.get('azure_documents', {}))
        nb_pieces = len(st.session_state.get('pieces_selectionnees', {}))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", nb_docs)
        with col2:
            st.metric("Pièces", nb_pieces)
        
        # Boutons utilitaires
        st.markdown("---")
        if st.button("🔄 Réinitialiser Azure", key="reinit_azure"):
            reinit_azure()
        
        if st.button("⚙️ Configuration", key="show_config"):
            st.session_state.show_config_modal = True
        
        # Mode développeur (temporaire pour debug)
        st.markdown("---")
        st.subheader("🧪 Outils de diagnostic")
        
        # NOUVEAU TOGGLE POUR VERIFY_ALL_FUNCTIONS
        run_verification = st.toggle(
            "🔍 Vérification complète de l'intégration",
            value=False,
            help="Lance une vérification approfondie de tous les modules et fonctions",
            key="run_module_verification"
        )
        
        if run_verification:
            st.info("🔧 Lancement de la vérification complète...")
            try:
                import verify_all_functions
                with st.container():
                    verify_all_functions.verify_function_integration()
            except ImportError:
                st.error("❌ Le fichier verify_all_functions.py n'est pas trouvé à la racine")
                st.info("💡 Assurez-vous d'avoir créé le fichier verify_all_functions.py à la racine du projet")
            except Exception as e:
                st.error(f"❌ Erreur lors de la vérification : {str(e)}")
                with st.expander("Détails de l'erreur"):
                    st.code(traceback.format_exc())
        
        # Mode développeur avancé
        if st.checkbox("🔧 Mode développeur avancé", key="advanced_dev_mode"):
            st.info("🛠️ Outils avancés activés")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 Quick Check", key="quick_check", use_container_width=True):
                    try:
                        # Vérification rapide inline
                        st.write("**Modules critiques:**")
                        modules_to_check = ['recherche', 'advanced_features', 'analyse_ia', 'bordereau']
                        for mod in modules_to_check:
                            try:
                                exec(f"import modules.{mod}")
                                st.success(f"✅ {mod}")
                            except:
                                st.error(f"❌ {mod}")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
            
            with col2:
                if st.button("🔍 Test Imports", key="test_imports", use_container_width=True):
                    try:
                        from modules import recherche
                        if hasattr(recherche, 'MODULE_FUNCTIONS'):
                            st.success(f"✅ {len(recherche.MODULE_FUNCTIONS)} fonctions")
                        else:
                            st.error("❌ MODULE_FUNCTIONS absent")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
            
            # NOUVELLE SECTION - Vérification complète des imports
            st.markdown("---")
            st.markdown("**🔧 Diagnostics avancés**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Vérifier tous les imports", key="full_import_check", use_container_width=True):
                    with st.spinner("Vérification en cours..."):
                        try:
                            from check_imports import check_all_imports
                            report = check_all_imports()
                            
                            # Afficher un résumé
                            if not report['errors']:
                                st.balloons()
                                st.success(f"✅ Tous les imports OK ({report['total_checked']} vérifiés)")
                            else:
                                st.error(f"❌ {len(report['errors'])} erreurs détectées")
                                for error in report['errors'][:3]:  # Afficher les 3 premières erreurs
                                    st.caption(f"• {error}")
                                if len(report['errors']) > 3:
                                    st.caption(f"... et {len(report['errors']) - 3} autres erreurs")
                                    
                        except ImportError:
                            st.error("❌ check_imports.py non trouvé")
                            st.info("💡 Créez le fichier check_imports.py à la racine du projet")
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")
            
            with col2:
                if st.button("📊 Rapport détaillé des imports", key="detailed_import_report", use_container_width=True):
                    with st.spinner("Génération du rapport..."):
                        try:
                            # Lancer check_imports.py comme une page séparée dans un nouvel onglet
                            st.info("💡 Pour un rapport détaillé, exécutez :")
                            st.code("streamlit run check_imports.py")
                            
                            # Ou afficher un résumé inline
                            from check_imports import check_all_imports
                            report = check_all_imports()
                            
                            # Créer un rapport textuel
                            report_text = f"""
RAPPORT DE VÉRIFICATION DES IMPORTS
==================================
✅ Modules OK: {len(report['success'])}
❌ Erreurs: {len(report['errors'])}
⚠️ Avertissements: {len(report['warnings'])}
DÉTAILS:
--------
"""
                            if report['errors']:
                                report_text += "\nERREURS:\n"
                                for e in report['errors']:
                                    report_text += f"- {e}\n"
                            
                            # Bouton de téléchargement
                            st.download_button(
                                label="💾 Télécharger le rapport",
                                data=report_text,
                                file_name=f"rapport_imports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain"
                            )
                        except Exception as e:
                            st.error(f"Erreur: {str(e)}")
            
            # Afficher le contenu de session_state
            if st.checkbox("📊 Voir session_state", key="show_session_state"):
                st.json({k: str(v)[:100] + "..." if len(str(v)) > 100 else str(v) 
                        for k, v in st.session_state.items()})
        
        # Si version classique, afficher les filtres
        if not use_simplified:
            # Filtres de recherche
            st.markdown("---")
            st.header("🔧 Filtres de recherche")
            
            # Filtre par type de document
            doc_type_filter = st.selectbox(
                "Type de document",
                ["Tous", "CONCLUSIONS", "PLAINTE", "ASSIGNATION", "COURRIER", "EXPERTISE"],
                index=0
            )
            
            # Filtre par date
            date_range = st.date_input(
                "Période",
                value=[],
                key="date_range"
            )
            
            # Filtre par partie
            partie_filter = st.text_input(
                "Nom de partie",
                placeholder="Ex: VINCI, SOGEPROM..."
            )
            
            # Filtre par infraction
            infraction_filter = st.multiselect(
                "Infractions",
                ["Abus de biens sociaux", "Corruption", "Escroquerie", "Abus de confiance", "Blanchiment"]
            )
        
        # Aide (commune aux deux versions)
        with st.expander("📚 Aide"):
            if use_simplified:
                st.markdown("""
                **Version unifiée :**
                
                Cette version combine :
                - ✅ L'analyse intelligente des requêtes
                - ✅ L'enrichissement automatique des parties
                - ✅ L'adaptation terminologique selon la phase
                - ✅ L'intégration de tous vos modules
                - ✅ Les fonctionnalités avancées
                
                **Exemples de commandes :**
                - `rédiger plainte contre Vinci, SOGEPROM @projet_26_05_2025`
                - `analyser les risques @dossier_pénal`
                - `créer bordereau @pièces_sélectionnées`
                - `jurisprudence corruption`
                - `synthétiser les pièces @dossier_fraude`
                """)
            else:
                st.markdown("""
                **Conseils de recherche:**
                
                🔹 **Référence dossier** : Utilisez @ suivi du code  
                   Ex: `@VINCI2024`
                
                🔹 **Recherche par partie** : Nom contre Nom  
                   Ex: `VINCI contre PERINET`
                
                🔹 **Type de document** : Ajoutez le type  
                   Ex: `conclusions @VINCI2024`
                
                🔹 **Infractions** : Mentionnez l'infraction  
                   Ex: `abus de biens sociaux SOGEPROM`
                
                🔹 **Recherche combinée** :  
                   Ex: `@VINCI2024 conclusions corruption`
                """)
    
    # ====== ROUTAGE SELON LA VERSION CHOISIE ======
    if use_simplified:
        # Afficher la version unifiée
        show_simplified_search()
    else:
        # Continuer avec l'interface classique
        # Zone de recherche principale
        st.markdown("<div class='search-container'>", unsafe_allow_html=True)
        
        # Créer un conteneur pour la barre de recherche
        search_container = st.container()
        
        # Gérer les valeurs initiales de recherche
        initial_value = ""
        if 'selected_suggestion' in st.session_state:
            initial_value = st.session_state.selected_suggestion
            del st.session_state.selected_suggestion
        elif 'pending_search' in st.session_state:
            initial_value = st.session_state.pending_search
            del st.session_state.pending_search
        
        with search_container:
            # Utilisation de form pour permettre la soumission avec Entrée
            with st.form(key="search_form", clear_on_submit=False):
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    # Champ de recherche avec placeholder informatif
                    search_query = st.text_input(
                        "Rechercher",
                        value=initial_value,
                        placeholder="Tapez votre recherche... (Ex: @VINCI2024 conclusions, abus de biens sociaux, etc.)",
                        label_visibility="hidden",
                        key="search_input"
                    )
                
                with col2:
                    # Bouton de recherche
                    search_button = st.form_submit_button(
                        "🔍 Rechercher",
                        use_container_width=True,
                        type="primary"
                    )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Afficher les suggestions (hors du form)
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        
        # Mettre à jour la requête si elle a changé
        if search_query and search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
            show_search_suggestions(search_query)
        
        # Construire les filtres
        filters = {}
        if doc_type_filter != "Tous":
            filters['document_type'] = doc_type_filter
        if partie_filter:
            filters['partie'] = partie_filter
        if infraction_filter:
            filters['infractions'] = infraction_filter
        if len(date_range) == 2:
            filters['date_range'] = date_range
        
        # Effectuer la recherche si le bouton est cliqué ou Entrée est pressée
        if search_button and search_query:
            # Stocker la requête dans session state
            st.session_state.last_search = search_query
            st.session_state.search_results = None
            
            # Analyser la requête pour extraire la référence @
            ref_match = re.search(r'@(\w+)', search_query)
            if ref_match:
                st.info(f"🎯 Recherche dans le dossier : **{ref_match.group(1)}**")
            
            # Effectuer la recherche
            try:
                results = asyncio.run(perform_search(search_query, filters))
                st.session_state.search_results = results
            except Exception as e:
                st.error(f"❌ Erreur lors de la recherche: {str(e)}")
                with st.expander("Détails de l'erreur"):
                    st.code(traceback.format_exc())
        
        # Afficher les résultats
        if 'search_results' in st.session_state and st.session_state.search_results:
            results = st.session_state.search_results
            
            # Statistiques de recherche
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Documents trouvés", results.total_count)
            with col2:
                st.metric("Documents affichés", len(results.documents))
            with col3:
                if 'last_search' in st.session_state:
                    st.metric("Dernière recherche", st.session_state.last_search[:20] + "...")
            
            # Afficher les suggestions si disponibles
            if hasattr(results, 'suggestions') and results.suggestions:
                display_search_suggestions(results.suggestions)
            
            # Afficher les facettes si disponibles
            if hasattr(results, 'facets') and results.facets:
                with st.expander("🔧 Affiner les résultats", expanded=False):
                    display_search_facets(results.facets)
            
            # Afficher les résultats
            st.markdown("## 📊 Résultats de recherche")
            
            if results.documents:
                # Filtrer selon les facettes actives si nécessaire
                filtered_docs = results.documents
                
                # Appliquer les filtres de score si activés
                if st.session_state.get('filter_high_score'):
                    filtered_docs = [d for d in filtered_docs if d.metadata.get('score', 0) >= 20]
                elif st.session_state.get('filter_medium_score'):
                    filtered_docs = [d for d in filtered_docs if 10 <= d.metadata.get('score', 0) < 20]
                elif st.session_state.get('filter_low_score'):
                    filtered_docs = [d for d in filtered_docs if d.metadata.get('score', 0) < 10]
                
                # Afficher les documents filtrés
                for idx, doc in enumerate(filtered_docs, 1):
                    display_result_enhanced(doc, idx)
                    if idx < len(filtered_docs):
                        st.markdown("---")
            else:
                st.warning("Aucun document trouvé pour cette recherche.")
            
            # Afficher les statistiques de recherche
            if st.button("📊 Voir les statistiques", key="show_stats"):
                stats = asyncio.run(get_search_service().get_search_statistics())
                with st.expander("Statistiques de recherche", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Recherches totales", stats['total_searches'])
                        st.metric("Résultats moyens", f"{stats['average_results']:.1f}")
                    with col2:
                        st.metric("Taille du cache", stats['cache_size'])
                        if stats['popular_keywords']:
                            st.write("**Mots-clés populaires:**")
                            for keyword, count in list(stats['popular_keywords'].items())[:5]:
                                st.write(f"• {keyword}: {count} fois")
    
    # Modal de document si nécessaire (commun aux deux versions)
    if st.session_state.get('show_document_modal'):
        show_document_modal()
    
    # Modal de configuration si demandé (commun aux deux versions)
    if st.session_state.get('show_config_modal', False):
        show_configuration_modal()
    
    # Footer avec informations
    st.markdown("---")
    st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# Point d'entrée
if __name__ == "__main__":
    try:
        # Initialiser les états de session si nécessaire
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        
        if 'azure_documents' not in st.session_state:
            st.session_state.azure_documents = {}
        
        if 'imported_documents' not in st.session_state:
            st.session_state.imported_documents = {}
        
        if 'pieces_selectionnees' not in st.session_state:
            st.session_state.pieces_selectionnees = {}
        
        # Lancer l'application
        main()
    except Exception as e:
        st.error("❌ ERREUR FATALE")
        st.code(str(e))
        st.code(traceback.format_exc())
        print("ERREUR FATALE:")
        print(traceback.format_exc()))