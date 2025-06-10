"""Gestionnaire Azure Search avec nouvel index"""

import os
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
import traceback

class AzureSearchManager:
    """Gestionnaire pour Azure Cognitive Search"""
    
    def __init__(self):
        """Initialise le gestionnaire Azure Search"""
        self.search_client = None
        self.index_client = None
        self.index_name = "search-rag-juridique"  # MODIFICATION : nouvel index
        self._connection_error = None
        
        # Récupérer les variables d'environnement
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        
        # Initialiser la connexion
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialise la connexion à Azure Search"""
        try:
            if not self.endpoint or not self.key:
                self._connection_error = "Variables d'environnement manquantes (AZURE_SEARCH_ENDPOINT ou AZURE_SEARCH_KEY)"
                return
            
            # Créer les credentials
            credential = AzureKeyCredential(self.key)
            
            # Créer le client pour l'index
            self.index_client = SearchIndexClient(
                endpoint=self.endpoint,
                credential=credential
            )
            
            # Créer le client de recherche
            self.search_client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=credential
            )
            
            # Tester la connexion
            self._test_connection()
            
        except Exception as e:
            self._connection_error = f"Erreur de connexion: {str(e)}"
            self.search_client = None
            self.index_client = None
    
    def _test_connection(self):
        """Teste la connexion en vérifiant l'existence de l'index"""
        try:
            # Vérifier que l'index existe
            indexes = self.index_client.list_indexes()
            index_names = [index.name for index in indexes]
            
            if self.index_name not in index_names:
                self._connection_error = f"Index '{self.index_name}' introuvable. Indexes disponibles: {', '.join(index_names)}"
                self.search_client = None
            else:
                self._connection_error = None
                
        except Exception as e:
            self._connection_error = f"Erreur lors du test de connexion: {str(e)}"
            self.search_client = None
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active"""
        return self.search_client is not None and self._connection_error is None
    
    def get_connection_error(self) -> Optional[str]:
        """Retourne l'erreur de connexion si elle existe"""
        return self._connection_error
    
    def search(self, query: str, top: int = 10, filters: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Effectue une recherche dans l'index
        
        Args:
            query: La requête de recherche
            top: Nombre maximum de résultats
            filters: Filtres OData optionnels
            
        Returns:
            Liste des documents trouvés
        """
        if not self.is_connected():
            return []
        
        try:
            # Paramètres de recherche
            search_params = {
                "search_text": query,
                "top": top,
                "include_total_count": True
            }
            
            if filters:
                search_params["filter"] = filters
            
            # Effectuer la recherche
            results = self.search_client.search(**search_params)
            
            # Convertir en liste
            documents = []
            for result in results:
                doc = dict(result)
                # Ajouter le score de recherche
                if hasattr(result, '@search.score'):
                    doc['search_score'] = getattr(result, '@search.score')
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un document spécifique par son ID
        
        Args:
            document_id: L'ID du document
            
        Returns:
            Le document ou None si non trouvé
        """
        if not self.is_connected():
            return None
        
        try:
            document = self.search_client.get_document(key=document_id)
            return dict(document)
        except Exception as e:
            print(f"Erreur lors de la récupération du document: {e}")
            return None
    
    def upload_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Upload des documents dans l'index
        
        Args:
            documents: Liste des documents à uploader
            
        Returns:
            True si succès, False sinon
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.search_client.upload_documents(documents=documents)
            return all(r.succeeded for r in result)
        except Exception as e:
            print(f"Erreur lors de l'upload des documents: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document de l'index
        
        Args:
            document_id: L'ID du document à supprimer
            
        Returns:
            True si succès, False sinon
        """
        if not self.is_connected():
            return False
        
        try:
            result = self.search_client.delete_documents(documents=[{"id": document_id}])
            return result[0].succeeded
        except Exception as e:
            print(f"Erreur lors de la suppression du document: {e}")
            return False
    
    def get_index_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques de l'index
        
        Returns:
            Dictionnaire avec les statistiques ou None
        """
        if not self.is_connected():
            return None
        
        try:
            # Récupérer le nombre de documents
            results = self.search_client.search(
                search_text="*",
                top=0,
                include_total_count=True
            )
            
            total_count = results.get_count()
            
            return {
                "index_name": self.index_name,
                "document_count": total_count,
                "endpoint": self.endpoint
            }
            
        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques: {e}")
            return None