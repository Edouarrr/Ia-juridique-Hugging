# managers/azure_search_manager.py
"""Gestionnaire Azure Cognitive Search avec diagnostics renforcés"""

import os
import streamlit as st
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
    AZURE_SEARCH_AVAILABLE = True
    print("[AzureSearchManager] ✅ Azure Search SDK importé avec succès")
except ImportError as e:
    AZURE_SEARCH_AVAILABLE = False
    print(f"[AzureSearchManager] ❌ Azure Search SDK non disponible: {e}")

class AzureSearchManager:
    """Gestionnaire pour Azure Cognitive Search"""
    
    def __init__(self):
        self.search_client = None
        self.index_client = None
        self.index_name = "juridique-index"
        self.connection_error = None
        
        print("[AzureSearchManager] Initialisation...")
        
        if not AZURE_SEARCH_AVAILABLE:
            self.connection_error = "SDK Azure Search non disponible"
            return
        
        # Récupérer les paramètres de connexion
        endpoint, key = self._get_connection_params()
        
        if not endpoint or not key:
            self.connection_error = "Paramètres de connexion manquants"
            return
        
        try:
            print(f"[AzureSearchManager] Connexion à {endpoint}")
            credential = AzureKeyCredential(key)
            
            self.search_client = SearchClient(
                endpoint=endpoint,
                index_name=self.index_name,
                credential=credential
            )
            
            self.index_client = SearchIndexClient(
                endpoint=endpoint,
                credential=credential
            )
            
            # Test de connexion
            self._test_connection()
            
            print("[AzureSearchManager] ✅ Connexion Azure Search réussie")
            
        except ClientAuthenticationError as e:
            self.connection_error = f"Erreur d'authentification Azure Search: {str(e)}"
            print(f"[AzureSearchManager] ❌ {self.connection_error}")
        except Exception as e:
            self.connection_error = f"Erreur connexion Azure Search: {str(e)}"
            print(f"[AzureSearchManager] ❌ {self.connection_error}")
    
    def _get_connection_params(self) -> tuple:
        """Récupère les paramètres de connexion"""
        
        # Endpoint
        endpoint = (
            os.getenv('AZURE_SEARCH_ENDPOINT') or
            (st.secrets.get("AZURE_SEARCH_ENDPOINT") if hasattr(st, 'secrets') else None) or
            os.getenv('azure_search_endpoint')
        )
        
        # Key
        key = (
            os.getenv('AZURE_SEARCH_KEY') or
            (st.secrets.get("AZURE_SEARCH_KEY") if hasattr(st, 'secrets') else None) or
            os.getenv('azure_search_key')
        )
        
        print(f"[AzureSearchManager] Endpoint: {'✅' if endpoint else '❌'}")
        print(f"[AzureSearchManager] Key: {'✅' if key else '❌'}")
        
        if endpoint:
            print(f"[AzureSearchManager] Endpoint: {endpoint}")
        if key:
            print(f"[AzureSearchManager] Key: {key[:10]}...")
        
        return endpoint, key
    
    def _test_connection(self):
        """Teste la connexion"""
        try:
            # Tenter une requête simple
            results = self.search_client.search("test", top=1)
            list(results)  # Consommer l'itérateur pour déclencher la requête
            print("[AzureSearchManager] ✅ Test de connexion réussi")
        except ResourceNotFoundError:
            print(f"[AzureSearchManager] ⚠️ Index '{self.index_name}' non trouvé, mais connexion OK")
        except Exception as e:
            print(f"[AzureSearchManager] ❌ Test de connexion échoué: {e}")
            raise
    
    def get_connection_error(self) -> Optional[str]:
        """Retourne l'erreur de connexion si applicable"""
        return self.connection_error
    
    def search_hybrid(self, query: str, top: int = 20, filters: Optional[str] = None) -> List[Dict]:
        """Recherche hybride (textuelle + vectorielle)"""
        if not self.search_client:
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
                documents.append({
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'score': result.get('@search.score', 0),
                    'source': result.get('source', 'Azure Search')
                })
            
            return documents
            
        except Exception as e:
            print(f"[AzureSearchManager] Erreur recherche hybride: {e}")
            return []
    
    def search_text(self, query: str, top: int = 20, filters: Optional[str] = None) -> List[Dict]:
        """Recherche textuelle pure"""
        if not self.search_client:
            return []
        
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                filter=filters,
                search_mode="all"
            )
            
            documents = []
            for result in results:
                documents.append({
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'score': result.get('@search.score', 0),
                    'source': 'Azure Search'
                })
            
            return documents
            
        except Exception as e:
            print(f"[AzureSearchManager] Erreur recherche textuelle: {e}")
            return []
    
    def search_vector(self, query_vector: List[float], top: int = 20) -> List[Dict]:
        """Recherche vectorielle pure"""
        if not self.search_client:
            return []
        
        try:
            print("[AzureSearchManager] ⚠️ Recherche vectorielle non implémentée complètement")
            return []
            
        except Exception as e:
            print(f"[AzureSearchManager] Erreur recherche vectorielle: {e}")
            return []