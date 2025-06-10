"""Gestionnaire Azure Search avec support vectoriel et recherche hybride"""

import os
from typing import List, Dict, Any, Optional, Tuple
from azure.core.credentials import AzureKeyCredential
import traceback
import logging

# Imports Azure Search
try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.models import (
        SearchMode,
        QueryType,
        VectorizedQuery,
        VectorFilterMode,
        HybridSearch,
        HybridCountAndFacetMode,
        RawVectorQuery
    )
    AZURE_SEARCH_AVAILABLE = True
except ImportError as e:
    AZURE_SEARCH_AVAILABLE = False
    print(f"[AzureSearchManager] ❌ Azure Search SDK non disponible: {e}")

logger = logging.getLogger(__name__)

class AzureSearchManager:
    """Gestionnaire pour Azure Cognitive Search avec support vectoriel"""
    
    def __init__(self):
        """Initialise le gestionnaire Azure Search"""
        self.search_client = None
        self.index_client = None
        self.index_name = "search-rag-juridique"  # Index avec support vectoriel
        self._connection_error = None
        self._index_fields = None
        self._has_vector_search = False
        self._vector_field_name = None
        
        print(f"[AzureSearchManager] Initialisation - AZURE_SEARCH_AVAILABLE: {AZURE_SEARCH_AVAILABLE}")
        
        if not AZURE_SEARCH_AVAILABLE:
            self._connection_error = "SDK Azure Search non disponible"
            return
        
        # Récupérer les variables d'environnement
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        
        # Méthodes alternatives pour récupérer les credentials
        if not self.endpoint or not self.key:
            try:
                import streamlit as st
                if hasattr(st, 'secrets'):
                    self.endpoint = self.endpoint or st.secrets.get('AZURE_SEARCH_ENDPOINT')
                    self.key = self.key or st.secrets.get('AZURE_SEARCH_KEY')
            except:
                pass
        
        # Initialiser la connexion
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialise la connexion à Azure Search"""
        try:
            if not self.endpoint or not self.key:
                self._connection_error = "Variables d'environnement manquantes (AZURE_SEARCH_ENDPOINT ou AZURE_SEARCH_KEY)"
                print(f"[AzureSearchManager] ❌ {self._connection_error}")
                return
            
            print(f"[AzureSearchManager] Endpoint: {self.endpoint}")
            print(f"[AzureSearchManager] Index: {self.index_name}")
            
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
            
            # Tester la connexion et analyser l'index
            self._test_connection()
            self._analyze_index_capabilities()
            
        except Exception as e:
            self._connection_error = f"Erreur de connexion: {str(e)}"
            self.search_client = None
            self.index_client = None
            logger.error(f"[AzureSearchManager] Erreur initialisation: {e}")
            print(f"[AzureSearchManager] ❌ {self._connection_error}")
    
    def _test_connection(self):
        """Teste la connexion en vérifiant l'existence de l'index"""
        try:
            # Vérifier que l'index existe
            indexes = list(self.index_client.list_indexes())
            index_names = [index.name for index in indexes]
            
            print(f"[AzureSearchManager] Indexes disponibles: {index_names}")
            
            if self.index_name not in index_names:
                self._connection_error = f"Index '{self.index_name}' introuvable. Indexes disponibles: {', '.join(index_names)}"
                self.search_client = None
                print(f"[AzureSearchManager] ❌ {self._connection_error}")
            else:
                self._connection_error = None
                print(f"[AzureSearchManager] ✅ Connexion réussie à l'index '{self.index_name}'")
                
        except Exception as e:
            self._connection_error = f"Erreur lors du test de connexion: {str(e)}"
            self.search_client = None
            print(f"[AzureSearchManager] ❌ {self._connection_error}")
    
    def _analyze_index_capabilities(self):
        """Analyse les capacités de l'index (champs vectoriels, etc.)"""
        if not self.search_client:
            return
        
        try:
            # Récupérer la définition de l'index
            index = self.index_client.get_index(self.index_name)
            self._index_fields = {field.name: field for field in index.fields}
            
            print(f"[AzureSearchManager] Champs de l'index: {list(self._index_fields.keys())}")
            
            # Détecter les champs vectoriels
            for field_name, field in self._index_fields.items():
                # Vérifier si c'est un champ vectoriel
                if hasattr(field, 'vector_search_dimensions') and field.vector_search_dimensions:
                    self._has_vector_search = True
                    self._vector_field_name = field_name
                    print(f"[AzureSearchManager] ✅ Champ vectoriel détecté: '{field_name}' ({field.vector_search_dimensions} dimensions)")
                    break
                
                # Alternative: vérifier le type du champ
                if hasattr(field, 'type') and 'vector' in str(field.type).lower():
                    self._has_vector_search = True
                    self._vector_field_name = field_name
                    print(f"[AzureSearchManager] ✅ Champ vectoriel détecté (par type): '{field_name}'")
                    break
            
            if not self._has_vector_search:
                print("[AzureSearchManager] ℹ️ Pas de champ vectoriel détecté - recherche textuelle uniquement")
                
        except Exception as e:
            logger.warning(f"[AzureSearchManager] Impossible d'analyser les capacités de l'index: {e}")
            print(f"[AzureSearchManager] ⚠️ Analyse de l'index échouée: {e}")
            self._index_fields = {}
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active"""
        return self.search_client is not None and self._connection_error is None
    
    def get_connection_error(self) -> Optional[str]:
        """Retourne l'erreur de connexion si elle existe"""
        return self._connection_error
    
    async def search(self, query: str, top: int = 10, filter_string: Optional[str] = None, 
                    vector_query: Optional[List[float]] = None, search_mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Effectue une recherche asynchrone dans l'index (compatible avec universal_search_service)
        
        Args:
            query: La requête de recherche textuelle
            top: Nombre maximum de résultats
            filter_string: Filtre OData
            vector_query: Vecteur de requête pour la recherche sémantique (optionnel)
            search_mode: Mode de recherche forcé ('vector', 'hybrid', 'text') ou None pour auto
            
        Returns:
            Liste des documents trouvés
        """
        # Déléguer à la méthode synchrone
        results, _ = self.search_sync(query, top, filter_string, vector_query, search_mode)
        return results
    
    def search(self, query: str, top: int = 10, filters: Optional[str] = None, 
               vector_query: Optional[List[float]] = None, search_mode: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Alias pour search_sync pour compatibilité"""
        return self.search_sync(query, top, filters, vector_query, search_mode)
    
    def search_sync(self, query: str, top: int = 10, filters: Optional[str] = None, 
                    vector_query: Optional[List[float]] = None, search_mode: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Effectue une recherche synchrone dans l'index avec support vectoriel/hybride/textuel
        
        Args:
            query: La requête de recherche textuelle
            top: Nombre maximum de résultats
            filters: Filtres OData optionnels
            vector_query: Vecteur de requête pour la recherche sémantique (optionnel)
            search_mode: Mode de recherche forcé ('vector', 'hybrid', 'text') ou None pour auto
            
        Returns:
            Tuple (Liste des documents trouvés, métadonnées de recherche)
        """
        if not self.is_connected():
            return [], {"error": self._connection_error}
        
        try:
            # Déterminer le mode de recherche
            if search_mode is None:
                search_mode = self._determine_search_mode(query, vector_query)
            
            logger.info(f"[AzureSearchManager] 🔍 Mode de recherche: {search_mode}")
            print(f"[AzureSearchManager] 🔍 Recherche '{query}' en mode: {search_mode}")
            
            # Paramètres de base
            search_params = {
                "top": top,
                "include_total_count": True,
                "select": "*"  # Récupérer tous les champs
            }
            
            if filters:
                search_params["filter"] = filters
            
            # Configuration selon le mode de recherche
            if search_mode == "vector" and vector_query and self._has_vector_search:
                # Recherche vectorielle pure
                print(f"[AzureSearchManager] Mode vectoriel avec {len(vector_query)} dimensions")
                vector_queries = [VectorizedQuery(
                    vector=vector_query,
                    k_nearest_neighbors=top,
                    fields=self._vector_field_name
                )]
                search_params["vector_queries"] = vector_queries
                
            elif search_mode == "hybrid" and vector_query and self._has_vector_search:
                # Recherche hybride (textuelle + vectorielle)
                print(f"[AzureSearchManager] Mode hybride")
                search_params["search_text"] = query
                search_params["query_type"] = QueryType.SEMANTIC
                
                # Essayer de trouver la configuration sémantique
                if hasattr(self, '_semantic_config_name'):
                    search_params["semantic_configuration_name"] = self._semantic_config_name
                else:
                    search_params["semantic_configuration_name"] = "default"
                
                vector_queries = [VectorizedQuery(
                    vector=vector_query,
                    k_nearest_neighbors=top,
                    fields=self._vector_field_name
                )]
                search_params["vector_queries"] = vector_queries
                
            else:
                # Recherche textuelle classique
                print(f"[AzureSearchManager] Mode textuel")
                search_params["search_text"] = query
                search_params["search_mode"] = SearchMode.ALL
                search_params["query_type"] = QueryType.SIMPLE
                
                # Activer la recherche sémantique si disponible
                if self._has_semantic_search():
                    search_params["query_type"] = QueryType.SEMANTIC
                    search_params["semantic_configuration_name"] = "default"
            
            # Effectuer la recherche
            print(f"[AzureSearchManager] Exécution de la recherche...")
            results = self.search_client.search(**search_params)
            
            # Traiter les résultats
            documents = []
            total_count = 0
            
            for result in results:
                doc = dict(result)
                
                # Ajouter les métadonnées de scoring
                if hasattr(result, '@search.score'):
                    doc['@search.score'] = getattr(result, '@search.score')
                    doc['search_score'] = doc['@search.score']  # Alias pour compatibilité
                
                if hasattr(result, '@search.reranker_score'):
                    doc['reranker_score'] = getattr(result, '@search.reranker_score')
                
                if hasattr(result, '@search.captions'):
                    captions = getattr(result, '@search.captions')
                    if captions:
                        doc['captions'] = [{'text': c.text, 'highlights': c.highlights} for c in captions]
                
                documents.append(doc)
            
            # Récupérer le nombre total
            if hasattr(results, 'get_count'):
                total_count = results.get_count()
            
            print(f"[AzureSearchManager] ✅ {len(documents)} résultats trouvés (total: {total_count})")
            
            # Métadonnées de recherche
            metadata = {
                "total_count": total_count,
                "search_mode": search_mode,
                "has_vector": vector_query is not None,
                "index_has_vector": self._has_vector_search
            }
            
            return documents, metadata
            
        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {e}"
            logger.error(f"[AzureSearchManager] {error_msg}")
            print(f"[AzureSearchManager] ❌ {error_msg}")
            return [], {"error": str(e)}
    
    def _determine_search_mode(self, query: str, vector_query: Optional[List[float]]) -> str:
        """Détermine automatiquement le mode de recherche optimal"""
        if vector_query and self._has_vector_search:
            # Si on a un vecteur et que l'index le supporte
            if query and len(query.strip()) > 0:
                return "hybrid"  # Recherche hybride si on a aussi du texte
            else:
                return "vector"  # Recherche vectorielle pure
        else:
            return "text"  # Recherche textuelle par défaut
    
    def _has_semantic_search(self) -> bool:
        """Vérifie si la recherche sémantique est disponible"""
        # Cette méthode pourrait être améliorée en vérifiant la configuration réelle
        # Pour l'instant, on suppose qu'elle est disponible si on a des champs vectoriels
        return self._has_vector_search
    
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
            print(f"[AzureSearchManager] Erreur lors de la récupération du document: {e}")
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
            success = all(r.succeeded for r in result)
            print(f"[AzureSearchManager] Upload de {len(documents)} documents: {'✅ Succès' if success else '❌ Échec'}")
            return success
        except Exception as e:
            print(f"[AzureSearchManager] ❌ Erreur lors de l'upload des documents: {e}")
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
            print(f"[AzureSearchManager] ❌ Erreur lors de la suppression du document: {e}")
            return False
    
    def list_containers(self) -> List[str]:
        """Pour compatibilité avec l'ancienne interface - retourne liste vide"""
        return []
    
    def get_index_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques détaillées de l'index
        
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
            
            total_count = results.get_count() if hasattr(results, 'get_count') else 0
            
            # Analyser les capacités
            capabilities = {
                "text_search": True,
                "vector_search": self._has_vector_search,
                "semantic_search": self._has_semantic_search(),
                "vector_field": self._vector_field_name
            }
            
            # Récupérer les champs disponibles
            field_names = list(self._index_fields.keys()) if self._index_fields else []
            
            return {
                "index_name": self.index_name,
                "document_count": total_count,
                "endpoint": self.endpoint,
                "capabilities": capabilities,
                "fields": field_names,
                "vector_dimensions": self._get_vector_dimensions()
            }
            
        except Exception as e:
            logger.error(f"[AzureSearchManager] Erreur lors de la récupération des statistiques: {e}")
            return None
    
    def _get_vector_dimensions(self) -> Optional[int]:
        """Récupère le nombre de dimensions du champ vectoriel"""
        if not self._has_vector_search or not self._vector_field_name or not self._index_fields:
            return None
        
        try:
            field = self._index_fields.get(self._vector_field_name)
            if field and hasattr(field, 'vector_search_dimensions'):
                return field.vector_search_dimensions
        except:
            pass
        
        return None
    
    def search_similar_documents(self, document_id: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche des documents similaires basée sur un document existant
        
        Args:
            document_id: ID du document de référence
            top: Nombre de résultats similaires
            
        Returns:
            Liste des documents similaires
        """
        if not self.is_connected():
            return []
        
        try:
            # Récupérer le document source
            source_doc = self.get_document(document_id)
            if not source_doc:
                return []
            
            # Si on a un champ vectoriel, utiliser la similarité vectorielle
            if self._has_vector_search and self._vector_field_name in source_doc:
                vector = source_doc[self._vector_field_name]
                documents, _ = self.search_sync(
                    query="",
                    top=top,
                    vector_query=vector,
                    search_mode="vector"
                )
                # Filtrer le document source des résultats
                return [doc for doc in documents if doc.get('id') != document_id]
            
            # Sinon, utiliser une recherche textuelle basée sur le contenu
            else:
                # Extraire du texte pertinent du document
                text_content = self._extract_searchable_text(source_doc)
                if text_content:
                    documents, _ = self.search_sync(
                        query=text_content[:500],  # Limiter la longueur
                        top=top + 1  # +1 car on va filtrer le document source
                    )
                    return [doc for doc in documents if doc.get('id') != document_id][:top]
            
            return []
            
        except Exception as e:
            logger.error(f"[AzureSearchManager] Erreur recherche documents similaires: {e}")
            return []
    
    def _extract_searchable_text(self, document: Dict[str, Any]) -> str:
        """Extrait le texte recherchable d'un document"""
        # Chercher les champs de contenu communs
        content_fields = ['content', 'text', 'description', 'title', 'body']
        
        for field in content_fields:
            if field in document and document[field]:
                return str(document[field])
        
        # Si aucun champ standard, concatener les valeurs textuelles
        text_parts = []
        for key, value in document.items():
            if isinstance(value, str) and len(value) > 10 and not key.startswith('_'):
                text_parts.append(value)
        
        return " ".join(text_parts[:3])  # Limiter à 3 champs
    
    def get_search_suggestions(self, query: str, top: int = 5) -> List[str]:
        """
        Obtient des suggestions de recherche basées sur la requête
        
        Args:
            query: Début de la requête
            top: Nombre de suggestions
            
        Returns:
            Liste de suggestions
        """
        if not self.is_connected() or len(query) < 2:
            return []
        
        try:
            # Utiliser la fonctionnalité de suggestion si disponible
            # Sinon, faire une recherche partielle
            results = self.search_client.search(
                search_text=f"{query}*",
                top=top * 2,
                search_mode=SearchMode.ALL,
                select="title,content"
            )
            
            suggestions = set()
            for result in results:
                # Extraire des mots-clés pertinents
                if 'title' in result:
                    suggestions.add(result['title'][:50])
                
            return list(suggestions)[:top]
            
        except Exception as e:
            logger.error(f"[AzureSearchManager] Erreur suggestions: {e}")
            return []