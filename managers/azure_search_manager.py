# managers/azure_search_manager.py
"""Gestionnaire Azure Cognitive Search"""

import os
import logging
from typing import List, Dict, Optional, Any
import streamlit as st

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.models import VectorizedQuery
    from azure.core.credentials import AzureKeyCredential
    AZURE_SEARCH_AVAILABLE = True
except ImportError:
    AZURE_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)

class AzureSearchManager:
    """Gère les opérations de recherche avec Azure Cognitive Search"""
    
    def __init__(self):
        """Initialise le gestionnaire de recherche"""
        self.search_client = None
        self.index_client = None
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX', 'juridique-index')
        
        if self.endpoint and self.key and AZURE_SEARCH_AVAILABLE:
            try:
                credential = AzureKeyCredential(self.key)
                
                # Client pour les opérations de recherche
                self.search_client = SearchClient(
                    endpoint=self.endpoint,
                    index_name=self.index_name,
                    credential=credential
                )
                
                # Client pour la gestion des index
                self.index_client = SearchIndexClient(
                    endpoint=self.endpoint,
                    credential=credential
                )
                
                logger.info("✅ Connexion Azure Search établie")
            except Exception as e:
                logger.error(f"❌ Erreur connexion Azure Search: {e}")
                st.warning(f"Impossible de se connecter à Azure Search: {str(e)}")
        else:
            if not AZURE_SEARCH_AVAILABLE:
                logger.warning("⚠️ Azure Search SDK non installé")
            else:
                logger.warning("⚠️ Configuration Azure Search manquante")
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est établie"""
        return self.search_client is not None
    
    def search_text(self, query: str, top: int = 20, filters: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche textuelle simple"""
        if not self.is_connected():
            return []
        
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                filter=filters,
                include_total_count=True
            )
            
            documents = []
            for result in results:
                doc = {
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'source': result.get('source', ''),
                    'score': result.get('@search.score', 0),
                    'metadata': result.get('metadata', {})
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Erreur recherche textuelle: {e}")
            return []
    
    def search_vector(self, query_embedding: List[float], top: int = 20, 
                     filters: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche vectorielle (sémantique)"""
        if not self.is_connected():
            return []
        
        try:
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top,
                fields="contentVector"
            )
            
            results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                filter=filters,
                top=top
            )
            
            documents = []
            for result in results:
                doc = {
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'source': result.get('source', ''),
                    'score': result.get('@search.score', 0),
                    'metadata': result.get('metadata', {})
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Erreur recherche vectorielle: {e}")
            return []
    
    def search_hybrid(self, query: str, query_embedding: Optional[List[float]] = None, 
                     top: int = 20, filters: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche hybride (textuelle + vectorielle)"""
        if not self.is_connected():
            return []
        
        try:
            # Si pas d'embedding fourni, faire une recherche textuelle simple
            if not query_embedding:
                return self.search_text(query, top, filters)
            
            # Recherche hybride
            vector_query = VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=top,
                fields="contentVector"
            )
            
            results = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=filters,
                top=top,
                include_total_count=True
            )
            
            documents = []
            for result in results:
                doc = {
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'source': result.get('source', ''),
                    'score': result.get('@search.score', 0),
                    'metadata': result.get('metadata', {})
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Erreur recherche hybride: {e}")
            # Fallback sur recherche textuelle
            return self.search_text(query, top, filters)
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """Indexe un document dans Azure Search"""
        if not self.is_connected():
            return False
        
        try:
            # S'assurer que le document a un ID
            if 'id' not in document:
                document['id'] = str(datetime.now().timestamp())
            
            # Uploader le document
            result = self.search_client.upload_documents(documents=[document])
            
            # Vérifier le résultat
            if result[0].succeeded:
                logger.info(f"✅ Document '{document['id']}' indexé")
                return True
            else:
                logger.error(f"❌ Échec indexation: {result[0].error}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur indexation document: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Supprime un document de l'index"""
        if not self.is_connected():
            return False
        
        try:
            result = self.search_client.delete_documents(documents=[{"id": document_id}])
            
            if result[0].succeeded:
                logger.info(f"✅ Document '{document_id}' supprimé")
                return True
            else:
                logger.error(f"❌ Échec suppression: {result[0].error}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur suppression document: {e}")
            return False
    
    def get_document_count(self) -> int:
        """Retourne le nombre de documents dans l'index"""
        if not self.is_connected():
            return 0
        
        try:
            # Recherche vide pour obtenir le count
            results = self.search_client.search(
                search_text="*",
                include_total_count=True,
                top=0
            )
            
            return results.get_count()
            
        except Exception as e:
            logger.error(f"Erreur comptage documents: {e}")
            return 0