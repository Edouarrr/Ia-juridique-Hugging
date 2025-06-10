"""Script de test pour Azure Search avec support vectoriel"""

import asyncio
import streamlit as st
from managers.azure_search_manager import AzureSearchManager
from managers.universal_search_service import UniversalSearchService

def test_azure_search_connection():
    """Test de connexion basique"""
    st.header("🔍 Test Azure Search")
    
    # Test du manager
    st.subheader("1. Test du gestionnaire Azure Search")
    
    manager = AzureSearchManager()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Connexion:**")
        if manager.is_connected():
            st.success("✅ Connecté")
        else:
            st.error(f"❌ Non connecté: {manager.get_connection_error()}")
    
    with col2:
        st.write("**Index:**")
        st.info(manager.index_name)
    
    # Statistiques
    if manager.is_connected():
        stats = manager.get_index_statistics()
        if stats:
            st.subheader("📊 Statistiques de l'index")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Documents", stats.get('document_count', 0))
            
            with col2:
                st.metric("Champs", len(stats.get('fields', [])))
            
            with col3:
                capabilities = stats.get('capabilities', {})
                modes = []
                if capabilities.get('text_search'):
                    modes.append("Texte")
                if capabilities.get('vector_search'):
                    modes.append("Vectoriel")
                if capabilities.get('semantic_search'):
                    modes.append("Sémantique")
                st.metric("Modes", ", ".join(modes))
            
            # Détails des capacités
            with st.expander("🔧 Capacités détaillées"):
                st.json(stats.get('capabilities', {}))
                
                if stats.get('vector_dimensions'):
                    st.info(f"Dimensions vectorielles: {stats['vector_dimensions']}")
                
                if stats.get('fields'):
                    st.write("**Champs disponibles:**")
                    for field in stats['fields'][:10]:
                        st.text(f"• {field}")
                    if len(stats['fields']) > 10:
                        st.text(f"... et {len(stats['fields']) - 10} autres")

async def test_search_modes():
    """Test des différents modes de recherche"""
    st.subheader("2. Test des modes de recherche")
    
    service = UniversalSearchService()
    
    # Interface de test
    query = st.text_input("Requête de test", value="abus de biens sociaux")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        test_text = st.button("🔤 Recherche textuelle", use_container_width=True)
    
    with col2:
        test_hybrid = st.button("🔀 Recherche hybride", use_container_width=True)
    
    with col3:
        test_vector = st.button("🧮 Recherche vectorielle", use_container_width=True)
    
    # Exécuter le test demandé
    if test_text:
        with st.spinner("Recherche textuelle en cours..."):
            results = await service.search(query, search_mode="text", top=5)
            display_results(results, "Textuelle")
    
    elif test_hybrid:
        with st.spinner("Recherche hybride en cours..."):
            results = await service.search(query, search_mode=None, top=5)  # Auto = hybride si possible
            display_results(results, "Hybride")
    
    elif test_vector:
        if service.embeddings_service:
            with st.spinner("Recherche vectorielle en cours..."):
                results = await service.search(query, search_mode="vector", top=5)
                display_results(results, "Vectorielle")
        else:
            st.warning("⚠️ Service d'embeddings non disponible")

def display_results(results, mode_name):
    """Affiche les résultats de recherche"""
    st.success(f"✅ Recherche {mode_name} terminée")
    
    # Métadonnées
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents trouvés", results.total_count)
    with col2:
        st.metric("Mode utilisé", results.search_mode)
    with col3:
        st.metric("Résultats affichés", len(results.documents))
    
    # Résultats
    if results.documents:
        st.markdown("### 📄 Résultats")
        
        for i, doc in enumerate(results.documents[:5], 1):
            with st.expander(f"{i}. {doc.title} (Score: {doc.score:.2f})"):
                st.write(f"**Source:** {doc.source}")
                st.write(f"**ID:** {doc.id}")
                
                if doc.metadata:
                    st.write("**Métadonnées:**")
                    st.json(doc.metadata)
                
                if doc.highlights:
                    st.write("**Extraits pertinents:**")
                    for highlight in doc.highlights:
                        st.info(f"...{highlight}...")
                
                st.write("**Contenu:**")
                st.text(doc.content[:500] + "..." if len(doc.content) > 500 else doc.content)
    
    # Facettes
    if results.facets:
        with st.expander("📊 Facettes"):
            st.json(results.facets)
    
    # Suggestions
    if results.suggestions:
        st.write("**💡 Suggestions:**")
        for suggestion in results.suggestions:
            st.caption(f"• {suggestion}")

def test_advanced_features():
    """Test des fonctionnalités avancées"""
    st.subheader("3. Fonctionnalités avancées")
    
    manager = AzureSearchManager()
    
    if not manager.is_connected():
        st.error("❌ Non connecté à Azure Search")
        return
    
    # Test de recherche avec filtres
    with st.expander("🔧 Test avec filtres"):
        col1, col2 = st.columns(2)
        
        with col1:
            query = st.text_input("Requête", value="corruption", key="filter_query")
            doc_type = st.selectbox("Type de document", ["", "CONCLUSIONS", "PLAINTE", "ASSIGNATION"])
        
        with col2:
            reference = st.text_input("Référence (@)", placeholder="VINCI2024")
            
            if st.button("🔍 Rechercher avec filtres"):
                filters = None
                if doc_type:
                    filters = f"documentType eq '{doc_type}'"
                if reference:
                    if filters:
                        filters += f" and reference eq '{reference}'"
                    else:
                        filters = f"reference eq '{reference}'"
                
                docs, meta = manager.search(query, filters=filters, top=3)
                
                st.write(f"**Résultats:** {len(docs)} documents")
                st.write(f"**Filtre appliqué:** `{filters}`")
                
                for doc in docs[:3]:
                    st.json(doc)
    
    # Test de documents similaires
    with st.expander("🔍 Test de recherche par similarité"):
        doc_id = st.text_input("ID du document de référence", key="similar_doc_id")
        
        if st.button("Trouver documents similaires") and doc_id:
            similar_docs = manager.search_similar_documents(doc_id, top=3)
            
            if similar_docs:
                st.success(f"✅ {len(similar_docs)} documents similaires trouvés")
                for doc in similar_docs:
                    st.json(doc)
            else:
                st.warning("Aucun document similaire trouvé")

# Interface principale
def main():
    st.set_page_config(page_title="Test Azure Search", page_icon="🔍", layout="wide")
    
    st.title("🔍 Test Azure Search - Recherche Vectorielle/Hybride")
    
    # Tests de base
    test_azure_search_connection()
    
    st.markdown("---")
    
    # Tests des modes de recherche
    asyncio.run(test_search_modes())
    
    st.markdown("---")
    
    # Tests avancés
    test_advanced_features()
    
    # Statistiques globales
    st.markdown("---")
    st.subheader("📊 Statistiques globales")
    
    service = UniversalSearchService()
    stats = asyncio.run(service.get_search_statistics())
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Recherches totales", stats.get('total_searches', 0))
        
        with col2:
            st.metric("Hits cache", f"{stats.get('cache_hit_rate', 0):.1f}%")
        
        with col3:
            st.metric("Taille cache", stats.get('cache_size', 0))
        
        with col4:
            modes = stats.get('search_modes', {})
            mode_str = f"T:{modes.get('text', 0)} H:{modes.get('hybrid', 0)} V:{modes.get('vector', 0)}"
            st.metric("Modes utilisés", mode_str)

if __name__ == "__main__":
    main()