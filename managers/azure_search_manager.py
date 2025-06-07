# managers/azure_search_manager.py
"""Gestionnaire pour Azure Cognitive Search"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Vérifier la disponibilité d'Azure
try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.models import VectorizedQuery
    from azure.core.credentials import AzureKeyCredential
    AZURE_SEARCH_AVAILABLE = True
except ImportError:
    AZURE_SEARCH_AVAILABLE = False
    logger.warning("Modules Azure Search non disponibles")

try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False
    logger.warning("Azure OpenAI non disponible")

from models.dataclasses import Document
from config.app_config import APP_CONFIG, SearchMode
from utils.helpers import clean_env_for_azure

class AzureSearchManager:
    """Gestionnaire pour Azure Cognitive Search avec vectorisation"""
    
    def __init__(self):
        self.search_client = None
        self.index_client = None
        self.openai_client = None
        try:
            self._init_clients()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation d'AzureSearchManager : {e}")
    
    def _init_clients(self):
        """Initialise les clients Azure Search et OpenAI"""
        try:
            # Nettoyer l'environnement
            clean_env_for_azure()
            
            # Azure Search
            search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
            search_key = os.getenv('AZURE_SEARCH_KEY')
            
            if search_endpoint and search_key and AZURE_SEARCH_AVAILABLE:
                self.index_client = SearchIndexClient(
                    endpoint=search_endpoint,
                    credential=AzureKeyCredential(search_key)
                )
                
                self.search_client = SearchClient(
                    endpoint=search_endpoint,
                    index_name=APP_CONFIG['SEARCH_INDEX_NAME'],
                    credential=AzureKeyCredential(search_key)
                )
                
                logger.info("Client Azure Search initialisé")
            
            # OpenAI pour les embeddings
            openai_key = os.getenv('AZURE_OPENAI_KEY')
            openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            
            if openai_key and openai_endpoint and AZURE_OPENAI_AVAILABLE:
                self.openai_client = AzureOpenAI(
                    azure_endpoint=openai_endpoint,
                    api_key=openai_key,
                    api_version="2024-02-01"
                )
                logger.info("Client OpenAI pour embeddings initialisé")
                
        except Exception as e:
            logger.error(f"Erreur initialisation Azure Search: {e}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Génère un embedding pour un texte"""
        if not self.openai_client:
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                input=text[:8000],
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return None
    
    def index_document(self, document: Document) -> bool:
        """Indexe un document avec son vecteur"""
        if not self.search_client:
            return False
        
        try:
            embedding = self.generate_embedding(f"{document.title} {document.content}")
            
            if not embedding:
                logger.warning(f"Pas d'embedding pour {document.id}")
                embedding = [0.0] * APP_CONFIG['VECTOR_DIMENSION']
            
            doc_to_index = {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "source": document.source,
                "embedding": embedding
            }
            
            self.search_client.upload_documents([doc_to_index])
            logger.info(f"Document {document.id} indexé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur indexation document: {e}")
            return False
    
    def search_hybrid(self, query: str, mode: SearchMode = SearchMode.HYBRID, 
                     top: int = 50, filters: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recherche hybride (textuelle + vectorielle)"""
        if not self.search_client:
            return []
        
        try:
            results = []
            
            if mode in [SearchMode.HYBRID, SearchMode.VECTOR_ONLY]:
                query_embedding = self.generate_embedding(query)
                
                if query_embedding:
                    vector_query = VectorizedQuery(
                        vector=query_embedding,
                        k_nearest_neighbors=top,
                        fields="embedding"
                    )
                    
                    if mode == SearchMode.VECTOR_ONLY:
                        response = self.search_client.search(
                            search_text=None,
                            vector_queries=[vector_query],
                            filter=filters,
                            top=top
                        )
                    else:
                        response = self.search_client.search(
                            search_text=query,
                            vector_queries=[vector_query],
                            filter=filters,
                            top=top
                        )
                    
                    for result in response:
                        results.append({
                            'id': result['id'],
                            'title': result['title'],
                            'content': result['content'],
                            'score': result['@search.score'],
                            'source': result['source']
                        })
            
            elif mode == SearchMode.TEXT_ONLY:
                response = self.search_client.search(
                    search_text=query,
                    filter=filters,
                    top=top
                )
                
                for result in response:
                    results.append({
                        'id': result['id'],
                        'title': result['title'],
                        'content': result['content'],
                        'score': result['@search.score'],
                        'source': result['source']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche hybride: {e}")
            return []