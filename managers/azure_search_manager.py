"""
Gestionnaire Azure Cognitive Search pour la recherche de documents juridiques
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import re
from dataclasses import dataclass, field

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import conditionnel d'Azure Search
try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SimpleField,
        SearchableField,
        SearchField,
        SearchFieldDataType,
        VectorSearch,
        HnswAlgorithmConfiguration,
        VectorSearchProfile,
        SemanticConfiguration,
        SemanticPrioritizedFields,
        SemanticField,
        SemanticSearch,
        ScoringProfile,
        TextWeights
    )
    from azure.search.documents.models import (
        VectorizedQuery,
        QueryType,
        QueryCaptionType,
        QueryAnswerType
    )
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
    AZURE_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.error(f"Azure Search SDK non disponible: {e}")
    AZURE_SEARCH_AVAILABLE = False
    # Classes de substitution pour éviter les erreurs
    SearchClient = None
    SearchIndexClient = None
    AzureKeyCredential = None

@dataclass
class SearchResult:
    """Résultat de recherche structuré"""
    id: str
    title: str
    content: str
    source: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)

class AzureSearchManager:
    """Gestionnaire pour Azure Cognitive Search"""
    
    def __init__(self):
        """Initialise le gestionnaire Azure Search"""
        self.search_client = None
        self.index_client = None
        self.index_name = os.getenv('AZURE_SEARCH_INDEX', 'juridique-index')
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_KEY')
        self.connection_error = None
        
        logger.info(f"Initialisation Azure Search - Index: {self.index_name}")
        
        if not AZURE_SEARCH_AVAILABLE:
            self.connection_error = "SDK Azure Search non disponible. Installez azure-search-documents."
            logger.error(self.connection_error)
            return
            
        if not self.endpoint or not self.key:
            self.connection_error = "Variables d'environnement AZURE_SEARCH_ENDPOINT et AZURE_SEARCH_KEY requises"
            logger.error(self.connection_error)
            return
            
        try:
            # Créer les clients Azure Search
            credential = AzureKeyCredential(self.key)
            
            self.search_client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=credential
            )
            
            self.index_client = SearchIndexClient(
                endpoint=self.endpoint,
                credential=credential
            )
            
            # Vérifier la connexion et créer l'index si nécessaire
            self._ensure_index_exists()
            
            logger.info(f"✅ Azure Search connecté avec succès à l'index '{self.index_name}'")
            
        except Exception as e:
            self.connection_error = f"Erreur de connexion Azure Search: {str(e)}"
            logger.error(self.connection_error)
            self.search_client = None
            self.index_client = None
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active"""
        return self.search_client is not None
    
    def get_connection_error(self) -> Optional[str]:
        """Retourne l'erreur de connexion s'il y en a une"""
        return self.connection_error
    
    def _ensure_index_exists(self):
        """Vérifie que l'index existe, le crée si nécessaire"""
        if not self.index_client:
            return
            
        try:
            # Vérifier si l'index existe
            self.index_client.get_index(self.index_name)
            logger.info(f"Index '{self.index_name}' existe déjà")
        except ResourceNotFoundError:
            # L'index n'existe pas, le créer
            logger.info(f"Création de l'index '{self.index_name}'...")
            self._create_index()
    
    def _create_index(self):
        """Crée l'index avec le schéma approprié"""
        if not AZURE_SEARCH_AVAILABLE or not self.index_client:
            return
            
        try:
            # Définir les champs de l'index
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String, 
                              searchable=True, filterable=True, sortable=True),
                SearchableField(name="content", type=SearchFieldDataType.String, 
                              searchable=True),
                SimpleField(name="source", type=SearchFieldDataType.String, 
                          filterable=True, facetable=True),
                SimpleField(name="document_type", type=SearchFieldDataType.String, 
                          filterable=True, facetable=True),
                SimpleField(name="date", type=SearchFieldDataType.DateTimeOffset, 
                          filterable=True, sortable=True),
                SimpleField(name="parties", type=SearchFieldDataType.Collection(SearchFieldDataType.String), 
                          filterable=True, facetable=True),
                SimpleField(name="infractions", type=SearchFieldDataType.Collection(SearchFieldDataType.String), 
                          filterable=True, facetable=True),
                SimpleField(name="reference", type=SearchFieldDataType.String, 
                          filterable=True),
                SimpleField(name="metadata", type=SearchFieldDataType.String),
                
                # Champ pour la recherche vectorielle (si nécessaire)
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,  # Pour OpenAI embeddings
                    vector_search_profile_name="myHnswProfile"
                )
            ]
            
            # Configuration de la recherche vectorielle
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="myHnsw",
                        parameters={
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="myHnswProfile",
                        algorithm_configuration_name="myHnsw"
                    )
                ]
            )
            
            # Configuration de la recherche sémantique
            semantic_config = SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")]
                )
            )
            
            semantic_search = SemanticSearch(configurations=[semantic_config])
            
            # Profils de scoring pour améliorer la pertinence
            scoring_profiles = [
                ScoringProfile(
                    name="titleBoost",
                    text_weights=TextWeights(
                        weights={"title": 2.0, "content": 1.0}
                    )
                )
            ]
            
            # Créer l'index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
                scoring_profiles=scoring_profiles,
                default_scoring_profile="titleBoost"
            )
            
            self.index_client.create_index(index)
            logger.info(f"✅ Index '{self.index_name}' créé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'index: {e}")
            raise
    
    def search(self, query: str, filters: Optional[Dict] = None, 
               top: int = 50, skip: int = 0,
               include_total_count: bool = True,
               search_mode: str = "any",
               query_type: str = "simple",
               use_semantic_search: bool = False) -> Dict[str, Any]:
        """
        Effectue une recherche dans l'index
        
        Args:
            query: Requête de recherche
            filters: Filtres OData optionnels
            top: Nombre maximum de résultats
            skip: Nombre de résultats à ignorer
            include_total_count: Inclure le nombre total
            search_mode: "any" ou "all"
            query_type: "simple", "full", ou "semantic"
            use_semantic_search: Utiliser la recherche sémantique
            
        Returns:
            Dictionnaire avec les résultats et métadonnées
        """
        if not self.search_client:
            return {
                "results": [],
                "total_count": 0,
                "error": "Client de recherche non initialisé"
            }
        
        try:
            # Construire les paramètres de recherche
            search_params = {
                "search_text": query,
                "top": top,
                "skip": skip,
                "include_total_count": include_total_count,
                "search_mode": search_mode,
                "query_type": QueryType.SIMPLE if query_type == "simple" else QueryType.FULL,
                "highlight_fields": "title,content",
                "highlight_pre_tag": "<mark>",
                "highlight_post_tag": "</mark>"
            }
            
            # Ajouter les filtres OData si fournis
            if filters:
                filter_expressions = []
                
                if "document_type" in filters:
                    filter_expressions.append(f"document_type eq '{filters['document_type']}'")
                
                if "partie" in filters:
                    filter_expressions.append(f"parties/any(p: p eq '{filters['partie']}')")
                
                if "infractions" in filters:
                    infraction_filters = [f"infractions/any(i: i eq '{inf}')" for inf in filters['infractions']]
                    filter_expressions.append(f"({' or '.join(infraction_filters)})")
                
                if "date_range" in filters and len(filters["date_range"]) == 2:
                    start_date = filters["date_range"][0].isoformat()
                    end_date = filters["date_range"][1].isoformat()
                    filter_expressions.append(f"date ge {start_date} and date le {end_date}")
                
                if filter_expressions:
                    search_params["filter"] = " and ".join(filter_expressions)
            
            # Ajouter la recherche sémantique si activée
            if use_semantic_search and query_type == "semantic":
                search_params["query_type"] = QueryType.SEMANTIC
                search_params["semantic_configuration_name"] = "my-semantic-config"
                search_params["query_caption"] = QueryCaptionType.EXTRACTIVE
                search_params["query_answer"] = QueryAnswerType.EXTRACTIVE
            
            # Effectuer la recherche
            results = self.search_client.search(**search_params)
            
            # Traiter les résultats
            search_results = []
            facets = {}
            
            for result in results:
                # Créer un objet SearchResult
                search_result = SearchResult(
                    id=result.get("id", ""),
                    title=result.get("title", "Sans titre"),
                    content=result.get("content", ""),
                    source=result.get("source", "Unknown"),
                    score=result.get("@search.score", 0.0),
                    metadata={
                        "document_type": result.get("document_type", ""),
                        "date": result.get("date", ""),
                        "parties": result.get("parties", []),
                        "infractions": result.get("infractions", []),
                        "reference": result.get("reference", "")
                    }
                )
                
                # Ajouter les highlights si disponibles
                if "@search.highlights" in result:
                    highlights = []
                    for field, values in result["@search.highlights"].items():
                        highlights.extend(values)
                    search_result.highlights = highlights
                
                search_results.append(search_result)
            
            # Récupérer les facettes si disponibles
            if hasattr(results, "facets") and results.facets:
                facets = dict(results.facets)
            
            # Récupérer le nombre total si disponible
            total_count = 0
            if hasattr(results, "get_count"):
                total_count = results.get_count() or len(search_results)
            
            return {
                "results": search_results,
                "total_count": total_count,
                "facets": facets,
                "query": query,
                "filters": filters
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return {
                "results": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """
        Indexe un document dans Azure Search
        
        Args:
            document: Document à indexer avec les champs requis
            
        Returns:
            True si succès, False sinon
        """
        if not self.search_client:
            logger.error("Client de recherche non initialisé")
            return False
        
        try:
            # Valider et préparer le document
            doc_to_index = {
                "id": document.get("id", ""),
                "title": document.get("title", ""),
                "content": document.get("content", ""),
                "source": document.get("source", ""),
                "document_type": document.get("document_type", "unknown"),
                "date": document.get("date", datetime.now().isoformat()),
                "parties": document.get("parties", []),
                "infractions": document.get("infractions", []),
                "reference": document.get("reference", ""),
                "metadata": json.dumps(document.get("metadata", {}))
            }
            
            # Ajouter le vecteur si fourni
            if "content_vector" in document:
                doc_to_index["content_vector"] = document["content_vector"]
            
            # Indexer le document
            result = self.search_client.upload_documents(documents=[doc_to_index])
            
            if result[0].succeeded:
                logger.info(f"Document {doc_to_index['id']} indexé avec succès")
                return True
            else:
                logger.error(f"Échec de l'indexation du document {doc_to_index['id']}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation: {e}")
            return False
    
    def index_documents_batch(self, documents: List[Dict[str, Any]], 
                            batch_size: int = 100) -> Tuple[int, int]:
        """
        Indexe plusieurs documents par batch
        
        Args:
            documents: Liste de documents à indexer
            batch_size: Taille des batchs
            
        Returns:
            Tuple (nombre de succès, nombre d'échecs)
        """
        if not self.search_client:
            logger.error("Client de recherche non initialisé")
            return 0, len(documents)
        
        success_count = 0
        failure_count = 0
        
        # Traiter par batch
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Préparer les documents
                docs_to_index = []
                for doc in batch:
                    doc_to_index = {
                        "id": doc.get("id", ""),
                        "title": doc.get("title", ""),
                        "content": doc.get("content", ""),
                        "source": doc.get("source", ""),
                        "document_type": doc.get("document_type", "unknown"),
                        "date": doc.get("date", datetime.now().isoformat()),
                        "parties": doc.get("parties", []),
                        "infractions": doc.get("infractions", []),
                        "reference": doc.get("reference", ""),
                        "metadata": json.dumps(doc.get("metadata", {}))
                    }
                    
                    if "content_vector" in doc:
                        doc_to_index["content_vector"] = doc["content_vector"]
                    
                    docs_to_index.append(doc_to_index)
                
                # Indexer le batch
                results = self.search_client.upload_documents(documents=docs_to_index)
                
                # Compter les succès et échecs
                for result in results:
                    if result.succeeded:
                        success_count += 1
                    else:
                        failure_count += 1
                        
            except Exception as e:
                logger.error(f"Erreur lors de l'indexation du batch: {e}")
                failure_count += len(batch)
        
        logger.info(f"Indexation terminée: {success_count} succès, {failure_count} échecs")
        return success_count, failure_count
    
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document de l'index
        
        Args:
            document_id: ID du document à supprimer
            
        Returns:
            True si succès, False sinon
        """
        if not self.search_client:
            return False
        
        try:
            result = self.search_client.delete_documents(documents=[{"id": document_id}])
            return result[0].succeeded
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False
    
    def get_document_count(self) -> int:
        """Retourne le nombre total de documents dans l'index"""
        if not self.search_client:
            return 0
        
        try:
            result = self.search_client.search(search_text="*", top=0, include_total_count=True)
            return result.get_count() or 0
        except Exception:
            return 0
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyse une requête pour extraire les éléments clés
        
        Args:
            query: Requête à analyser
            
        Returns:
            Dictionnaire avec les éléments extraits
        """
        analysis = {
            "original_query": query,
            "reference": None,
            "document_types": [],
            "parties": [],
            "keywords": [],
            "infractions": []
        }
        
        # Extraire la référence @
        ref_match = re.search(r'@(\w+)', query)
        if ref_match:
            analysis["reference"] = ref_match.group(1)
            query = query.replace(ref_match.group(0), "")
        
        # Détecter les types de documents
        doc_types = ["conclusions", "plainte", "assignation", "courrier", "expertise", "jugement"]
        for doc_type in doc_types:
            if doc_type.lower() in query.lower():
                analysis["document_types"].append(doc_type)
        
        # Détecter les infractions
        infractions = [
            "abus de biens sociaux", "corruption", "escroquerie", 
            "abus de confiance", "blanchiment", "faux", "recel"
        ]
        for infraction in infractions:
            if infraction.lower() in query.lower():
                analysis["infractions"].append(infraction)
        
        # Extraire les parties (mots en majuscules)
        parties = re.findall(r'\b[A-Z]{3,}\b', query)
        analysis["parties"] = list(set(parties))
        
        # Extraire les mots-clés restants
        keywords = query.split()
        keywords = [k for k in keywords if len(k) > 2 and k not in analysis["parties"]]
        analysis["keywords"] = keywords
        
        return analysis
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """
        Retourne des suggestions basées sur une requête partielle
        
        Args:
            partial_query: Début de requête
            
        Returns:
            Liste de suggestions
        """
        suggestions = []
        
        if not self.search_client or len(partial_query) < 2:
            return suggestions
        
        try:
            # Rechercher avec autocomplete si disponible
            results = self.search_client.search(
                search_text=f"{partial_query}*",
                top=5,
                search_mode="all",
                select="title,reference"
            )
            
            for result in results:
                if result.get("title"):
                    suggestions.append(result["title"])
                if result.get("reference") and result["reference"] not in suggestions:
                    suggestions.append(f"@{result['reference']}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de suggestions: {e}")
        
        return suggestions[:5]  # Limiter à 5 suggestions