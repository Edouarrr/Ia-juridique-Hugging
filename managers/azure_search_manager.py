# managers/azure_search_manager.py
"""Gestionnaire Azure Cognitive Search avec recherche intelligente et vectorisation"""

import os
import streamlit as st
from typing import List, Dict, Optional, Any, Union
import logging
import json

logger = logging.getLogger(__name__)

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
    from azure.search.documents.models import (
        VectorizedQuery,
        VectorQuery,
        QueryType,
        QueryLanguage,
        SearchMode
    )
    AZURE_SEARCH_AVAILABLE = True
    print("[AzureSearchManager] ✅ Azure Search SDK importé avec succès")
except ImportError as e:
    AZURE_SEARCH_AVAILABLE = False
    print(f"[AzureSearchManager] ❌ Azure Search SDK non disponible: {e}")

# Import des embeddings si disponible
try:
    from openai import OpenAI
    EMBEDDINGS_AVAILABLE = True
    print("[AzureSearchManager] ✅ OpenAI SDK disponible pour embeddings")
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("[AzureSearchManager] ⚠️ OpenAI SDK non disponible pour embeddings")

class AzureSearchManager:
    """Gestionnaire pour Azure Cognitive Search avec recherche intelligente"""
    
    def __init__(self):
        self.search_client = None
        self.index_client = None
        self.index_name = "search-rag-juridique"  # MODIFICATION: nouvel index
        self.connection_error = None
        self.embeddings_client = None
        self.index_schema = None
        
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
            
            # Test de connexion et récupération du schéma
            self._test_connection()
            self._get_index_schema()
            
            # Initialiser le client d'embeddings si disponible
            self._initialize_embeddings()
            
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
    
    def _get_index_schema(self):
        """Récupère le schéma de l'index pour déterminer les capacités"""
        try:
            index = self.index_client.get_index(self.index_name)
            self.index_schema = {
                'name': index.name,
                'fields': {},
                'has_vector_fields': False,
                'vector_field_names': [],
                'semantic_config': None
            }
            
            # Analyser les champs
            for field in index.fields:
                field_info = {
                    'name': field.name,
                    'type': str(field.type),
                    'searchable': field.searchable,
                    'filterable': field.filterable,
                    'facetable': field.facetable
                }
                
                # Vérifier si c'est un champ vectoriel
                if hasattr(field, 'vector_search_dimensions') and field.vector_search_dimensions:
                    field_info['is_vector'] = True
                    field_info['dimensions'] = field.vector_search_dimensions
                    self.index_schema['has_vector_fields'] = True
                    self.index_schema['vector_field_names'].append(field.name)
                
                self.index_schema['fields'][field.name] = field_info
            
            # Vérifier la configuration sémantique
            if hasattr(index, 'semantic_search') and index.semantic_search:
                self.index_schema['semantic_config'] = index.semantic_search
            
            print(f"[AzureSearchManager] Schéma de l'index récupéré:")
            print(f"  - Champs vectoriels: {self.index_schema['vector_field_names']}")
            print(f"  - Recherche sémantique: {'✅' if self.index_schema['semantic_config'] else '❌'}")
            
        except Exception as e:
            print(f"[AzureSearchManager] ⚠️ Impossible de récupérer le schéma: {e}")
    
    def _initialize_embeddings(self):
        """Initialise le client d'embeddings pour la vectorisation"""
        if not EMBEDDINGS_AVAILABLE:
            print("[AzureSearchManager] ⚠️ Embeddings non disponibles (OpenAI SDK manquant)")
            return
        
        # Récupérer la clé API OpenAI
        api_key = (
            os.getenv('OPENAI_API_KEY') or
            (st.secrets.get("OPENAI_API_KEY") if hasattr(st, 'secrets') else None)
        )
        
        if api_key:
            try:
                self.embeddings_client = OpenAI(api_key=api_key)
                print("[AzureSearchManager] ✅ Client d'embeddings initialisé")
            except Exception as e:
                print(f"[AzureSearchManager] ⚠️ Erreur initialisation embeddings: {e}")
        else:
            print("[AzureSearchManager] ⚠️ Clé API OpenAI non trouvée pour embeddings")
    
    def get_connection_error(self) -> Optional[str]:
        """Retourne l'erreur de connexion si applicable"""
        return self.connection_error
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Génère un embedding pour le texte donné"""
        if not self.embeddings_client:
            return None
        
        try:
            response = self.embeddings_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[AzureSearchManager] Erreur génération embedding: {e}")
            return None
    
    def search(self, query: str, top: int = 20, filters: Optional[str] = None, 
               search_mode: Optional[str] = None) -> List[Dict]:
        """
        Recherche intelligente qui adapte automatiquement le mode selon les capacités
        
        Args:
            query: La requête de recherche
            top: Nombre de résultats
            filters: Filtres OData optionnels
            search_mode: Mode forcé ('text', 'vector', 'hybrid', 'semantic') ou None pour auto
            
        Returns:
            Liste des documents trouvés
        """
        if not self.search_client:
            return []
        
        # Déterminer le meilleur mode de recherche
        if search_mode is None:
            if self.index_schema and self.index_schema.get('has_vector_fields') and self.embeddings_client:
                search_mode = 'hybrid'  # Préférer hybride si disponible
            elif self.index_schema and self.index_schema.get('semantic_config'):
                search_mode = 'semantic'
            else:
                search_mode = 'text'
        
        print(f"[AzureSearchManager] Mode de recherche: {search_mode}")
        
        # Router vers la bonne méthode
        if search_mode == 'hybrid':
            return self.search_hybrid(query, top, filters)
        elif search_mode == 'vector':
            return self.search_vector(query, top, filters)
        elif search_mode == 'semantic':
            return self.search_semantic(query, top, filters)
        else:
            return self.search_text(query, top, filters)
    
    def search_hybrid(self, query: str, top: int = 20, filters: Optional[str] = None) -> List[Dict]:
        """Recherche hybride (textuelle + vectorielle)"""
        if not self.search_client:
            return []
        
        try:
            # Générer l'embedding pour la requête
            query_vector = self._generate_embedding(query)
            
            if query_vector and self.index_schema and self.index_schema['vector_field_names']:
                # Recherche hybride avec vecteur
                vector_field = self.index_schema['vector_field_names'][0]
                
                # Créer la requête vectorielle
                vector_query = VectorizedQuery(
                    vector=query_vector,
                    k_nearest_neighbors=top,
                    fields=vector_field
                )
                
                results = self.search_client.search(
                    search_text=query,
                    vector_queries=[vector_query],
                    top=top,
                    filter=filters,
                    query_type=QueryType.SIMPLE,
                    include_total_count=True
                )
            else:
                # Fallback vers recherche textuelle si pas de vecteur
                print("[AzureSearchManager] Fallback vers recherche textuelle (pas de vecteur)")
                return self.search_text(query, top, filters)
            
            documents = []
            for result in results:
                doc = self._format_result(result)
                doc['search_type'] = 'hybrid'
                documents.append(doc)
            
            print(f"[AzureSearchManager] Recherche hybride: {len(documents)} résultats")
            return documents
            
        except Exception as e:
            print(f"[AzureSearchManager] Erreur recherche hybride: {e}")
            # Fallback vers recherche textuelle
            return self.search_text(query, top, filters)
    
    def search_text(self, query: str, top: int = 20, filters: Optional[str] = None) -> List[Dict]:
        """Recherche textuelle pure"""
        if not self.search_client:
            return []
        
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                filter=filters,
                search_mode=SearchMode.ALL,
                query_type=QueryType.SIMPLE,
                include_total_count=True
            )
            
            documents = []
            for result in results:
                doc = self._format_result(result)
                doc['search_type'] = 'text'
                documents.append(doc)
            
            print(f"[AzureSearchManager] Recherche textuelle: {len(documents)} résultats")
            return documents
            
        except Exception as e:
            print(f"[AzureSearchManager] Erreur recherche textuelle: {e}")
            return []
    
    def search_vector(self, query: str, top: int = 20, filters: Optional[str] = None) -> List[Dict]:
        """Recherche vectorielle pure"""
        if not self.search_client or not self.embeddings_client:
            print("[AzureSearchManager] Recherche vectorielle impossible (pas d'embeddings)")
            return []
        
        try:
            # Générer l'embedding
            query_vector = self._generate_embedding(query)
            if not query_vector:
                return []
            
            # Trouver le champ vectoriel
            if not self.index_schema or not self.index_schema['vector_field_names']:
                print("[AzureSearchManager] Pas de champ vectoriel dans l'index")
                return []
            
            vector_field = self.index_schema['vector_field_names'][0]
            
            # Créer la requête vectorielle
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top,
                fields=vector_field
            )
            
            results = self.search_client.search(
                search_text=None,  # Pas de recherche textuelle
                vector_queries=[vector_query],
                top=top,
                filter=filters
            )
            
            documents = []
            for result in results:
                doc = self._format_result(result)
                doc['search_type'] = 'vector'
                documents.append(doc)
            
            print(f"[AzureSearchManager] Recherche vectorielle: {len(documents)} résultats")
            return documents
            
        except Exception as e:
            print(f"[AzureSearchManager] Erreur recherche vectorielle: {e}")
            return []
    
    def search_semantic(self, query: str, top: int = 20, filters: Optional[str] = None) -> List[Dict]:
        """Recherche sémantique (si configurée dans l'index)"""
        if not self.search_client:
            return []
        
        try:
            # Vérifier si la recherche sémantique est disponible
            if not self.index_schema or not self.index_schema.get('semantic_config'):
                print("[AzureSearchManager] Recherche sémantique non configurée, fallback textuelle")
                return self.search_text(query, top, filters)
            
            results = self.search_client.search(
                search_text=query,
                top=top,
                filter=filters,
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="default",  # Ou le nom de votre config
                query_language=QueryLanguage.FR_FR,  # Français
                include_total_count=True
            )
            
            documents = []
            for result in results:
                doc = self._format_result(result)
                doc['search_type'] = 'semantic'
                
                # Ajouter les captions sémantiques si disponibles
                if hasattr(result, '@search.captions') and getattr(result, '@search.captions'):
                    captions = getattr(result, '@search.captions')
                    doc['semantic_captions'] = [
                        {
                            'text': caption.text,
                            'highlights': caption.highlights if hasattr(caption, 'highlights') else []
                        }
                        for caption in captions
                    ]
                
                documents.append(doc)
            
            print(f"[AzureSearchManager] Recherche sémantique: {len(documents)} résultats")
            return documents
            
        except Exception as e:
            print(f"[AzureSearchManager] Erreur recherche sémantique: {e}, fallback textuelle")
            return self.search_text(query, top, filters)
    
    def _format_result(self, result: Any) -> Dict:
        """Formate un résultat de recherche"""
        doc = {
            'id': result.get('id', ''),
            'title': result.get('title', '') or result.get('nom', '') or result.get('filename', ''),
            'content': result.get('content', '') or result.get('contenu', ''),
            'source': result.get('source', 'Azure Search'),
            'metadata': {}
        }
        
        # Score de recherche
        if hasattr(result, '@search.score'):
            doc['score'] = getattr(result, '@search.score')
        
        # Highlights
        if hasattr(result, '@search.highlights'):
            highlights = getattr(result, '@search.highlights')
            if highlights:
                doc['highlights'] = []
                for field, values in highlights.items():
                    doc['highlights'].extend(values)
        
        # Métadonnées supplémentaires
        for key, value in result.items():
            if key not in ['id', 'title', 'content', 'source', 'nom', 'filename', 'contenu']:
                doc['metadata'][key] = value
        
        return doc
    
    def get_index_capabilities(self) -> Dict[str, Any]:
        """Retourne les capacités de l'index"""
        return {
            'index_name': self.index_name,
            'has_vector_search': bool(self.index_schema and self.index_schema['has_vector_fields']),
            'has_semantic_search': bool(self.index_schema and self.index_schema['semantic_config']),
            'has_embeddings': bool(self.embeddings_client),
            'vector_fields': self.index_schema['vector_field_names'] if self.index_schema else [],
            'available_modes': self._get_available_search_modes()
        }
    
    def _get_available_search_modes(self) -> List[str]:
        """Détermine les modes de recherche disponibles"""
        modes = ['text']  # Toujours disponible
        
        if self.index_schema:
            if self.index_schema.get('semantic_config'):
                modes.append('semantic')
            
            if self.index_schema.get('has_vector_fields'):
                if self.embeddings_client:
                    modes.extend(['vector', 'hybrid'])
                else:
                    print("[AzureSearchManager] Champs vectoriels présents mais pas d'embeddings")
        
        return modes