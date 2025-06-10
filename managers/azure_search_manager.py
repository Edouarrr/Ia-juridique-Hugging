"""Service de recherche universelle avec support vectoriel/hybride/textuel"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging
import streamlit as st

# Import du gestionnaire Azure Search
from .azure_search_manager import AzureSearchManager

logger = logging.getLogger(__name__)

@dataclass
class SearchDocument:
    """Représente un document de résultat de recherche"""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)
    score: float = 0.0

@dataclass
class SearchResults:
    """Conteneur pour les résultats de recherche"""
    documents: List[SearchDocument]
    total_count: int
    search_mode: str
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class UniversalSearchService:
    """Service unifié pour la recherche avec support multi-modes"""
    
    def __init__(self):
        """Initialise le service de recherche"""
        self.azure_search = AzureSearchManager()
        self._embeddings_cache = {}
        self._search_cache = {}
        self._stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'search_modes': {'text': 0, 'vector': 0, 'hybrid': 0}
        }
        
        # Initialiser le service d'embeddings si disponible
        self._init_embeddings_service()
    
    def _init_embeddings_service(self):
        """Initialise le service d'embeddings pour la recherche vectorielle"""
        self.embeddings_service = None
        
        try:
            # Essayer d'utiliser OpenAI embeddings si disponible
            openai_key = st.session_state.get('openai_api_key') or st.secrets.get('OPENAI_API_KEY')
            if openai_key:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_key)
                self.embeddings_service = "openai"
                logger.info("✅ Service d'embeddings OpenAI initialisé")
                return
        except Exception as e:
            logger.warning(f"Impossible d'initialiser OpenAI embeddings: {e}")
        
        # Essayer Azure OpenAI si disponible
        try:
            azure_openai_key = st.secrets.get('AZURE_OPENAI_KEY')
            azure_openai_endpoint = st.secrets.get('AZURE_OPENAI_ENDPOINT')
            if azure_openai_key and azure_openai_endpoint:
                from openai import AzureOpenAI
                self.azure_openai_client = AzureOpenAI(
                    api_key=azure_openai_key,
                    api_version="2024-02-01",
                    azure_endpoint=azure_openai_endpoint
                )
                self.embeddings_service = "azure_openai"
                logger.info("✅ Service d'embeddings Azure OpenAI initialisé")
                return
        except Exception as e:
            logger.warning(f"Impossible d'initialiser Azure OpenAI embeddings: {e}")
        
        logger.info("ℹ️ Pas de service d'embeddings disponible - recherche textuelle uniquement")
    
    async def search(self, query: str, filters: Optional[Dict] = None, 
                    top: int = 10, search_mode: Optional[str] = None) -> SearchResults:
        """
        Effectue une recherche universelle
        
        Args:
            query: Requête de recherche
            filters: Filtres optionnels
            top: Nombre de résultats
            search_mode: Mode forcé ou None pour auto
            
        Returns:
            SearchResults avec documents et métadonnées
        """
        # Statistiques
        self._stats['total_searches'] += 1
        
        # Vérifier le cache
        cache_key = f"{query}_{filters}_{top}_{search_mode}"
        if cache_key in self._search_cache:
            self._stats['cache_hits'] += 1
            logger.info(f"🎯 Résultat trouvé dans le cache")
            return self._search_cache[cache_key]
        
        # Prétraiter la requête
        processed_query, extracted_filters = self._process_query(query)
        
        # Combiner les filtres
        combined_filters = self._combine_filters(filters, extracted_filters)
        
        # Obtenir l'embedding si possible
        query_vector = None
        if self.embeddings_service and search_mode != "text":
            query_vector = await self._get_embedding(processed_query)
        
        # Construire le filtre Azure Search
        azure_filter = self._build_azure_filter(combined_filters)
        
        # Effectuer la recherche
        documents, metadata = self.azure_search.search(
            query=processed_query,
            top=top,
            filters=azure_filter,
            vector_query=query_vector,
            search_mode=search_mode
        )
        
        # Statistiques du mode
        actual_mode = metadata.get('search_mode', 'text')
        self._stats['search_modes'][actual_mode] += 1
        
        # Convertir en SearchDocuments
        search_documents = []
        for doc in documents:
            search_doc = self._convert_to_search_document(doc)
            search_documents.append(search_doc)
        
        # Générer les facettes
        facets = self._generate_facets(search_documents)
        
        # Générer les suggestions
        suggestions = self._generate_suggestions(query, search_documents)
        
        # Créer les résultats
        results = SearchResults(
            documents=search_documents,
            total_count=metadata.get('total_count', len(documents)),
            search_mode=actual_mode,
            facets=facets,
            suggestions=suggestions,
            metadata=metadata
        )
        
        # Mettre en cache
        self._search_cache[cache_key] = results
        
        return results
    
    def _process_query(self, query: str) -> Tuple[str, Dict]:
        """
        Prétraite la requête et extrait les filtres intégrés
        
        Returns:
            Tuple (requête nettoyée, filtres extraits)
        """
        filters = {}
        processed_query = query
        
        # Extraire les références @ (dossiers)
        ref_pattern = r'@(\w+)'
        refs = re.findall(ref_pattern, query)
        if refs:
            filters['references'] = refs
            processed_query = re.sub(ref_pattern, '', processed_query)
        
        # Extraire les types de documents
        doc_types = ['conclusions', 'plainte', 'assignation', 'courrier', 'expertise']
        for doc_type in doc_types:
            if doc_type.lower() in query.lower():
                filters['document_type'] = doc_type.upper()
                processed_query = processed_query.replace(doc_type, '')
        
        # Extraire les parties (pattern "X contre Y")
        contre_pattern = r'(\w+)\s+contre\s+(\w+)'
        contre_match = re.search(contre_pattern, query, re.IGNORECASE)
        if contre_match:
            filters['parties'] = [contre_match.group(1), contre_match.group(2)]
            processed_query = re.sub(contre_pattern, '', processed_query, flags=re.IGNORECASE)
        
        # Nettoyer la requête
        processed_query = ' '.join(processed_query.split())
        
        return processed_query.strip(), filters
    
    def _combine_filters(self, filters1: Optional[Dict], filters2: Dict) -> Dict:
        """Combine deux ensembles de filtres"""
        combined = filters2.copy()
        if filters1:
            for key, value in filters1.items():
                if key not in combined:
                    combined[key] = value
                elif isinstance(value, list) and isinstance(combined[key], list):
                    combined[key].extend(value)
        return combined
    
    def _build_azure_filter(self, filters: Dict) -> Optional[str]:
        """Construit un filtre OData pour Azure Search"""
        if not filters:
            return None
        
        filter_parts = []
        
        # Filtre par référence
        if 'references' in filters:
            ref_filters = [f"reference eq '{ref}'" for ref in filters['references']]
            filter_parts.append(f"({' or '.join(ref_filters)})")
        
        # Filtre par type de document
        if 'document_type' in filters:
            filter_parts.append(f"documentType eq '{filters['document_type']}'")
        
        # Filtre par parties
        if 'parties' in filters:
            partie_filters = [f"search.in(parties, '{partie}')" for partie in filters['parties']]
            filter_parts.append(f"({' and '.join(partie_filters)})")
        
        # Filtre par date
        if 'date_range' in filters and len(filters['date_range']) == 2:
            start_date, end_date = filters['date_range']
            filter_parts.append(f"date ge {start_date.isoformat()} and date le {end_date.isoformat()}")
        
        return ' and '.join(filter_parts) if filter_parts else None
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Obtient l'embedding d'un texte"""
        if not self.embeddings_service or not text:
            return None
        
        # Vérifier le cache
        if text in self._embeddings_cache:
            return self._embeddings_cache[text]
        
        try:
            if self.embeddings_service == "openai":
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                embedding = response.data[0].embedding
                
            elif self.embeddings_service == "azure_openai":
                response = self.azure_openai_client.embeddings.create(
                    model="text-embedding-ada-002",  # Ajuster selon votre déploiement
                    input=text
                )
                embedding = response.data[0].embedding
                
            else:
                return None
            
            # Mettre en cache
            self._embeddings_cache[text] = embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return None
    
    def _convert_to_search_document(self, doc: Dict[str, Any]) -> SearchDocument:
        """Convertit un document Azure Search en SearchDocument"""
        # Extraire les champs principaux
        doc_id = doc.get('id', '')
        title = doc.get('title', doc.get('fileName', 'Document sans titre'))
        content = doc.get('content', doc.get('text', ''))
        source = doc.get('source', doc.get('containerName', 'Inconnue'))
        
        # Extraire les métadonnées
        metadata = {
            'score': doc.get('search_score', 0.0),
            'reranker_score': doc.get('reranker_score'),
            'type': doc.get('documentType', doc.get('type', 'unknown')),
            'date': doc.get('date', doc.get('lastModified')),
            'parties': doc.get('parties', []),
            'reference': doc.get('reference'),
            'container': doc.get('containerName'),
            'path': doc.get('blobPath', doc.get('path'))
        }
        
        # Nettoyer les métadonnées nulles
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        # Extraire les highlights/captions
        highlights = []
        if 'captions' in doc:
            for caption in doc['captions']:
                if 'highlights' in caption:
                    highlights.extend(caption['highlights'])
                else:
                    highlights.append(caption['text'])
        
        return SearchDocument(
            id=doc_id,
            title=title,
            content=content,
            source=source,
            metadata=metadata,
            highlights=highlights[:3],  # Limiter à 3 highlights
            score=metadata.get('score', 0.0)
        )
    
    def _generate_facets(self, documents: List[SearchDocument]) -> Dict[str, Dict[str, int]]:
        """Génère des facettes à partir des résultats"""
        facets = {
            'sources': {},
            'types': {},
            'scores': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        for doc in documents:
            # Facette source
            source = doc.source
            facets['sources'][source] = facets['sources'].get(source, 0) + 1
            
            # Facette type
            doc_type = doc.metadata.get('type', 'unknown')
            facets['types'][doc_type] = facets['types'].get(doc_type, 0) + 1
            
            # Facette score
            if doc.score >= 20:
                facets['scores']['high'] += 1
            elif doc.score >= 10:
                facets['scores']['medium'] += 1
            else:
                facets['scores']['low'] += 1
        
        return facets
    
    def _generate_suggestions(self, query: str, documents: List[SearchDocument]) -> List[str]:
        """Génère des suggestions basées sur les résultats"""
        suggestions = []
        
        # Suggestions basées sur les facettes
        if documents:
            # Top sources
            sources = {}
            for doc in documents:
                sources[doc.source] = sources.get(doc.source, 0) + 1
            
            top_source = max(sources.items(), key=lambda x: x[1])[0]
            suggestions.append(f"{query} dans {top_source}")
            
            # Types de documents
            types = set(doc.metadata.get('type', '') for doc in documents[:5])
            types.discard('unknown')
            types.discard('')
            
            if types:
                for doc_type in list(types)[:2]:
                    suggestions.append(f"{doc_type.lower()} {query}")
        
        return suggestions[:3]
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de recherche"""
        stats = self._stats.copy()
        
        # Ajouter les stats Azure
        azure_stats = self.azure_search.get_index_statistics()
        if azure_stats:
            stats.update(azure_stats)
        
        # Calculer des métriques
        if stats['total_searches'] > 0:
            stats['cache_hit_rate'] = (stats['cache_hits'] / stats['total_searches']) * 100
            stats['average_results'] = 0  # À implémenter
        
        stats['cache_size'] = len(self._search_cache)
        stats['embeddings_cache_size'] = len(self._embeddings_cache)
        
        return stats
    
    def clear_cache(self):
        """Vide les caches"""
        self._search_cache.clear()
        self._embeddings_cache.clear()
        logger.info("✅ Caches vidés")