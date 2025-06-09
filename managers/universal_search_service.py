# managers/universal_search_service.py
"""Service de recherche universelle avec améliorations UX - Version optimisée"""

from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import difflib

# Classes de données nécessaires
class Partie:
    """Classe représentant une partie dans un dossier"""
    def __init__(self, id: str, nom: str, type_partie: str, type_personne: str, phase_procedure: Any):
        self.id = id
        self.nom = nom
        self.type_partie = type_partie
        self.type_personne = type_personne
        self.phase_procedure = phase_procedure
        self.info_entreprise = None

class Document:
    """Classe représentant un document"""
    def __init__(self, id: str, title: str, content: str, source: str, metadata: Dict = None):
        self.id = id
        self.title = title
        self.content = content
        self.source = source
        self.metadata = metadata or {}
        self.highlights = []  # Pour stocker les extraits pertinents

class QueryAnalysis:
    """Analyse détaillée d'une requête de recherche"""
    def __init__(self, original_query: str, query_lower: str, timestamp: datetime):
        self.original_query = original_query
        self.query_lower = query_lower
        self.timestamp = timestamp
        self.reference = None
        self.document_type = None
        self.action = None
        self.subject_matter = None
        self.phase_procedurale = None
        self.parties = {'demandeurs': [], 'defendeurs': []}
        self.infractions = []
        self.style_request = None
        self.date_filter = None
        self.keywords = []
        self.search_type = 'general'  # general, dossier, jurisprudence, partie
        self.command_type = None  # Pour le routing

class SearchResult:
    """Résultat de recherche enrichi"""
    def __init__(self, documents: List[Document], query: str, total_count: int):
        self.documents = documents
        self.query = query
        self.total_count = total_count
        self.timestamp = datetime.now()
        self.facets = {}  # Pour stocker des statistiques sur les résultats
        self.suggestions = []  # Suggestions de recherches alternatives

class UniversalSearchService:
    """Service unifié pour toutes les recherches dans l'application"""
    
    # Patterns centralisés pour éviter la duplication
    DEMANDEURS_PATTERNS = [
        ('interconstruction', 'INTERCONSTRUCTION'),
        ('vinci', 'VINCI'),
        ('sogeprom', 'SOGEPROM RÉALISATIONS'),
        ('demathieu bard', 'DEMATHIEU BARD'),
        ('demathieu', 'DEMATHIEU BARD'),
        ('bouygues', 'BOUYGUES'),
        ('eiffage', 'EIFFAGE'),
        ('spie', 'SPIE BATIGNOLLES'),
        ('leon grosse', 'LEON GROSSE'),
        ('fayat', 'FAYAT'),
        ('colas', 'COLAS'),
        ('eurovia', 'EUROVIA'),
        ('razel-bec', 'RAZEL-BEC'),
        ('nge', 'NGE'),
        ('gtm', 'GTM Bâtiment')
    ]
    
    DEFENDEURS_PATTERNS = [
        ('perinet', 'M. PERINET'),
        ('périnet', 'M. PÉRINET'),
        ('vp invest', 'VP INVEST'),
        ('perraud', 'M. PERRAUD'),
        ('martin', 'M. MARTIN'),
        ('dupont', 'M. DUPONT'),
        ('durand', 'M. DURAND'),
        ('laurent', 'M. LAURENT'),
        ('michel', 'M. MICHEL')
    ]
    
    INFRACTIONS_MAP = {
        'escroquerie': 'Escroquerie',
        'abus de confiance': 'Abus de confiance',
        'abus de biens sociaux': 'Abus de biens sociaux',
        'abs': 'Abus de biens sociaux',
        'faux': 'Faux et usage de faux',
        'corruption': 'Corruption',
        'trafic d\'influence': 'Trafic d\'influence',
        'favoritisme': 'Favoritisme',
        'prise illégale': 'Prise illégale d\'intérêts',
        'blanchiment': 'Blanchiment',
        'fraude fiscale': 'Fraude fiscale',
        'travail dissimulé': 'Travail dissimulé',
        'marchandage': 'Marchandage',
        'entrave': 'Entrave',
        'banqueroute': 'Banqueroute',
        'recel': 'Recel'
    }
    
    DOCUMENT_TYPES = {
        r'\b(conclusions?|conclusion)\b': 'CONCLUSIONS',
        r'\b(plaintes?|dépôt de plainte)\b': 'PLAINTE',
        r'\b(assignations?|citation)\b': 'ASSIGNATION',
        r'\b(courriers?|lettre|correspondance)\b': 'COURRIER',
        r'\b(contrats?|convention)\b': 'CONTRAT',
        r'\b(factures?|facturation)\b': 'FACTURE',
        r'\b(expertises?|rapport d\'expert)\b': 'EXPERTISE',
        r'\b(jugements?|décision|arrêt)\b': 'JUGEMENT'
    }
    
    def __init__(self):
        """Initialisation du service avec cache et optimisations"""
        self._cache = {}
        self._search_history = []
        self._common_terms = set(['le', 'la', 'les', 'de', 'des', 'un', 'une', 'et', 'ou', 'à', 'dans', 'pour'])
        self._executor = ThreadPoolExecutor(max_workers=3)
        
        # Dictionnaire des synonymes juridiques
        self.synonyms = {
            'abs': ['abus de biens sociaux', 'abus biens sociaux'],
            'conclusions': ['conclusion', 'conclusions récapitulatives'],
            'assignation': ['assignations', 'citation'],
            'defendeur': ['défendeur', 'défendeurs', 'partie adverse'],
            'demandeur': ['demandeurs', 'requérant', 'plaignant']
        }
    
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> SearchResult:
        """
        Recherche universelle optimisée avec cache et parallélisation
        
        Args:
            query: Requête de recherche
            filters: Filtres optionnels
            
        Returns:
            SearchResult avec documents et métadonnées
        """
        # Vérifier le cache
        cache_key = f"{query}_{str(filters)}"
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            # Vérifier si le cache est récent (moins de 5 minutes)
            if (datetime.now() - cached_result.timestamp).seconds < 300:
                return cached_result
        
        # Analyser la requête
        query_analysis = self.analyze_query_advanced(query)
        
        # Recherches parallèles dans différentes sources
        search_tasks = []
        
        # Tâche 1: Recherche locale
        local_task = self._search_local_documents(query_analysis, filters)
        search_tasks.append(local_task)
        
        # Tâche 2: Recherche Azure
        azure_task = self._search_azure_documents(query_analysis, filters)
        search_tasks.append(azure_task)
        
        # Tâche 3: Recherche dans l'historique si référence @
        if query_analysis.reference:
            history_task = self._search_reference_history(query_analysis.reference)
            search_tasks.append(history_task)
        
        # Exécuter toutes les recherches en parallèle
        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Combiner les résultats
        combined_results = []
        for result in all_results:
            if isinstance(result, list):
                combined_results.extend(result)
        
        # Déduplication et scoring intelligent
        unique_results = self._deduplicate_results(combined_results)
        scored_results = self._intelligent_scoring(unique_results, query_analysis)
        
        # Extraction des highlights
        highlighted_results = self._extract_highlights(scored_results, query_analysis)
        
        # Tri par pertinence
        sorted_results = sorted(highlighted_results, key=lambda x: x.get('score', 0), reverse=True)
        
        # Limiter les résultats et créer des documents
        top_results = sorted_results[:50]
        documents = [self._convert_to_document(r) for r in top_results]
        
        # Créer les facettes pour filtrage dynamique
        facets = self._create_facets(sorted_results)
        
        # Générer des suggestions
        suggestions = self._generate_suggestions(query_analysis, len(sorted_results))
        
        # Créer le résultat final
        result = SearchResult(
            documents=documents,
            query=query,
            total_count=len(sorted_results)
        )
        result.facets = facets
        result.suggestions = suggestions
        
        # Mettre en cache
        self._cache[cache_key] = result
        
        # Ajouter à l'historique
        self._search_history.append({
            'query': query,
            'timestamp': datetime.now(),
            'results_count': len(sorted_results)
        })
        
        return result
    
    def analyze_query_advanced(self, query: str) -> QueryAnalysis:
        """Analyse avancée de la requête avec extraction d'entités et détection de commande"""
        
        analysis = QueryAnalysis(
            original_query=query,
            query_lower=query.lower(),
            timestamp=datetime.now()
        )
        
        # Détection du type de commande pour le routing
        self._detect_command_type(analysis)
        
        # Extraction de la référence @ avec pattern amélioré
        ref_patterns = [
            r'@([A-Za-z0-9_\-]+)',  # Pattern standard
            r'dossier\s+([A-Za-z0-9_\-]+)',  # "dossier XXXX"
            r'affaire\s+([A-Za-z0-9_\-]+)',  # "affaire XXXX"
        ]
        
        for pattern in ref_patterns:
            ref_match = re.search(pattern, query, re.IGNORECASE)
            if ref_match:
                analysis.reference = ref_match.group(1).upper()
                analysis.search_type = 'dossier'
                break
        
        # Détection du type de document
        for pattern, doc_type in self.DOCUMENT_TYPES.items():
            if re.search(pattern, analysis.query_lower):
                analysis.document_type = doc_type
                break
        
        # Extraction intelligente des parties
        analysis.parties = self._extract_parties_advanced(query)
        
        # Extraction des infractions avec synonymes
        analysis.infractions = self._extract_infractions_advanced(query)
        
        # Extraction des mots-clés significatifs
        analysis.keywords = self._extract_keywords(query)
        
        # Détection du type de recherche
        if 'jurisprudence' in analysis.query_lower:
            analysis.search_type = 'jurisprudence'
        elif analysis.parties['demandeurs'] or analysis.parties['defendeurs']:
            analysis.search_type = 'partie'
        
        return analysis
    
    def _detect_command_type(self, analysis: QueryAnalysis):
        """Détecte le type de commande pour le routing"""
        query_lower = analysis.query_lower
        
        # Détection des commandes principales
        if any(word in query_lower for word in ['rédige', 'rédiger', 'écrire', 'créer', 'plainte', 'conclusions', 'courrier', 'assignation']):
            analysis.command_type = 'redaction'
            if 'plainte' in query_lower:
                analysis.command_type = 'plainte'
        elif any(word in query_lower for word in ['plaidoirie', 'plaider', 'audience']):
            analysis.command_type = 'plaidoirie'
        elif any(word in query_lower for word in ['préparer client', 'préparation', 'coaching']):
            analysis.command_type = 'preparation_client'
        elif any(word in query_lower for word in ['import', 'importer', 'charger', 'upload']):
            analysis.command_type = 'import'
        elif any(word in query_lower for word in ['export', 'exporter', 'télécharger', 'download']):
            analysis.command_type = 'export'
        elif any(word in query_lower for word in ['email', 'envoyer', 'mail', 'courrier électronique']):
            analysis.command_type = 'email'
        elif any(word in query_lower for word in ['analyser', 'analyse', 'étudier', 'examiner']):
            analysis.command_type = 'analysis'
        elif any(word in query_lower for word in ['sélectionner pièces', 'pièces', 'sélection']):
            analysis.command_type = 'piece_selection'
        elif 'bordereau' in query_lower:
            analysis.command_type = 'bordereau'
        elif any(word in query_lower for word in ['synthèse', 'synthétiser', 'résumer']):
            analysis.command_type = 'synthesis'
        elif any(word in query_lower for word in ['template', 'modèle', 'gabarit']):
            analysis.command_type = 'template'
        elif any(word in query_lower for word in ['jurisprudence', 'juris', 'décision', 'arrêt']):
            analysis.command_type = 'jurisprudence'
        elif any(word in query_lower for word in ['chronologie', 'timeline', 'frise']):
            analysis.command_type = 'timeline'
        elif any(word in query_lower for word in ['cartographie', 'mapping', 'carte', 'réseau']):
            analysis.command_type = 'mapping'
        elif any(word in query_lower for word in ['comparer', 'comparaison', 'différences']):
            analysis.command_type = 'comparison'
        else:
            analysis.command_type = 'search'
    
    def extract_parties_from_query(self, query: str) -> Dict[str, List[str]]:
        """Méthode publique pour extraire les parties d'une requête"""
        return self._extract_parties_advanced(query)
    
    def extract_infractions_from_query(self, query: str) -> List[str]:
        """Méthode publique pour extraire les infractions d'une requête"""
        return self._extract_infractions_advanced(query)
    
    def _extract_parties_advanced(self, query: str) -> Dict[str, List[str]]:
        """Extraction avancée des parties avec patterns multiples"""
        
        parties = {'demandeurs': [], 'defendeurs': []}
        query_lower = query.lower()
        
        # Méthode 1 : Recherche avec "pour" et "contre"
        if ' pour ' in query_lower and ' contre ' in query_lower:
            # Extraire la partie entre "pour" et "contre" pour les demandeurs
            partie_pour = query_lower.split(' pour ')[1].split(' contre ')[0]
            # Extraire la partie après "contre" pour les défendeurs
            partie_contre = query_lower.split(' contre ')[1]
            
            # Chercher les demandeurs dans la partie "pour"
            for keyword, nom_formate in self.DEMANDEURS_PATTERNS:
                if keyword in partie_pour:
                    parties['demandeurs'].append(nom_formate)
            
            # Chercher les défendeurs dans la partie "contre"
            for keyword, nom_formate in self.DEFENDEURS_PATTERNS:
                if keyword in partie_contre:
                    parties['defendeurs'].append(nom_formate)
        
        # Méthode 2 : Si pas de structure claire, recherche globale
        else:
            # Identifier d'abord les défendeurs (souvent après "contre")
            if ' contre ' in query_lower:
                partie_contre = query_lower.split(' contre ')[1]
                for keyword, nom_formate in self.DEFENDEURS_PATTERNS:
                    if keyword in partie_contre:
                        parties['defendeurs'].append(nom_formate)
            
            # Puis identifier les demandeurs dans le reste
            for keyword, nom_formate in self.DEMANDEURS_PATTERNS:
                if keyword in query_lower and nom_formate not in parties['defendeurs']:
                    # Vérifier que ce n'est pas dans la partie "contre"
                    if ' contre ' not in query_lower or keyword not in query_lower.split(' contre ')[1]:
                        parties['demandeurs'].append(nom_formate)
        
        # Patterns alternatifs pour identifier les relations entre parties
        patterns = [
            (r'(.+?)\s+c(?:ontre)?\.?\s+(.+)', 'versus'),  # X contre Y, X c. Y
            (r'(.+?)\s+vs?\.?\s+(.+)', 'versus'),  # X vs Y, X v. Y
            (r'demandeur[s]?\s*:\s*(.+?)(?:\s*défendeur|$)', 'demandeur'),
            (r'défendeur[s]?\s*:\s*(.+?)(?:\s*demandeur|$)', 'defendeur'),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if pattern_type == 'versus':
                    # Nettoyer et extraire les noms
                    demandeur_text = match.group(1).strip()
                    defendeur_text = match.group(2).strip()
                    
                    # Extraire les entités des textes
                    parties['demandeurs'].extend(self._extract_entity_names(demandeur_text))
                    parties['defendeurs'].extend(self._extract_entity_names(defendeur_text))
                elif pattern_type == 'demandeur':
                    parties['demandeurs'].extend(self._extract_entity_names(match.group(1)))
                elif pattern_type == 'defendeur':
                    parties['defendeurs'].extend(self._extract_entity_names(match.group(1)))
        
        # Déduplication
        parties['demandeurs'] = list(set(parties['demandeurs']))
        parties['defendeurs'] = list(set(parties['defendeurs']))
        
        return parties
    
    def _extract_entity_names(self, text: str) -> List[str]:
        """Extrait les noms d'entités d'un texte"""
        
        entities = []
        
        # Patterns pour les entités communes
        entity_patterns = [
            r'\b(VINCI|SOGEPROM|BOUYGUES|EIFFAGE)\b',  # Entreprises connues
            r'\b(M\.|Mme|Mr|Monsieur|Madame)\s+([A-Z][A-Za-z]+)\b',  # Personnes physiques
            r'\b(SAS|SARL|SA|SCI|EURL)\s+([A-Z][A-Za-z\s]+?)(?:\s|$)',  # Sociétés
            r'\b([A-Z][A-Z\s&]+?)(?:\s+(?:contre|c\.|vs?\.)|$)',  # Noms en majuscules
        ]
        
        for pattern in entity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = match.group(0).strip()
                if len(entity) > 2 and entity not in self._common_terms:
                    entities.append(entity)
        
        return entities
    
    def _extract_infractions_advanced(self, query: str) -> List[str]:
        """Extraction des infractions avec gestion des synonymes"""
        
        query_lower = query.lower()
        infractions = []
        
        for keyword, infraction in self.INFRACTIONS_MAP.items():
            if keyword in query_lower and infraction not in infractions:
                infractions.append(infraction)
        
        return infractions
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrait les mots-clés significatifs de la requête"""
        
        # Retirer les mots communs et la ponctuation
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = []
        
        for word in words:
            if (len(word) > 2 and 
                word not in self._common_terms and 
                not word.isdigit()):
                keywords.append(word)
        
        return keywords
    
    async def _search_reference_history(self, reference: str) -> List[Dict]:
        """Recherche dans l'historique des documents d'une référence"""
        
        results = []
        
        try:
            import streamlit as st
            
            # Rechercher dans tous les documents stockés
            all_docs = {}
            all_docs.update(st.session_state.get('azure_documents', {}))
            all_docs.update(st.session_state.get('imported_documents', {}))
            
            for doc_id, doc in all_docs.items():
                # Vérifier si le document appartient à la référence
                if reference.lower() in doc.get('title', '').lower() or \
                   reference.lower() in doc.get('content', '').lower():
                    results.append({
                        'id': doc_id,
                        'title': doc.get('title', 'Sans titre'),
                        'content': doc.get('content', ''),
                        'source': f"Dossier {reference}",
                        'type': 'reference_match',
                        'score': 10  # Score élevé pour les correspondances de référence
                    })
        except:
            pass
        
        return results
    
    async def _search_local_documents(self, query_analysis: QueryAnalysis, filters: Optional[Dict] = None) -> List[Dict]:
        """Recherche optimisée dans les documents locaux"""
        
        results = []
        
        try:
            import streamlit as st
            
            # Collecter tous les documents
            all_documents = {}
            all_documents.update(st.session_state.get('azure_documents', {}))
            all_documents.update(st.session_state.get('imported_documents', {}))
            
            # Recherche parallèle avec ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for doc_id, doc in all_documents.items():
                    future = executor.submit(
                        self._check_document_match,
                        doc_id, doc, query_analysis, filters
                    )
                    futures.append(future)
                
                # Collecter les résultats
                for future in futures:
                    match_result = future.result()
                    if match_result:
                        results.append(match_result)
        
        except ImportError:
            pass
        
        return results
    
    async def _search_azure_documents(self, query_analysis: QueryAnalysis, filters: Optional[Dict] = None) -> List[Dict]:
        """Recherche Azure optimisée"""
        
        results = []
        
        try:
            import streamlit as st
            search_manager = st.session_state.get('azure_search_manager')
            
            if search_manager and hasattr(search_manager, 'search'):
                # Construire une requête optimisée pour Azure
                search_terms = []
                
                # Ajouter la référence si présente
                if query_analysis.reference:
                    search_terms.append(query_analysis.reference)
                
                # Ajouter les mots-clés importants
                search_terms.extend(query_analysis.keywords[:5])
                
                # Ajouter les parties
                for partie in query_analysis.parties['demandeurs'][:2] + query_analysis.parties['defendeurs'][:2]:
                    search_terms.append(partie)
                
                # Construire la requête
                azure_query = ' '.join(search_terms)
                
                # Construire les filtres Azure
                azure_filters = []
                if filters:
                    if 'document_type' in filters:
                        azure_filters.append(f"documentType eq '{filters['document_type']}'")
                    if 'date_range' in filters and len(filters['date_range']) == 2:
                        start_date = filters['date_range'][0].isoformat()
                        end_date = filters['date_range'][1].isoformat()
                        azure_filters.append(f"date ge {start_date} and date le {end_date}")
                
                # Effectuer la recherche
                azure_results = await search_manager.search(
                    azure_query,
                    filter_string=' and '.join(azure_filters) if azure_filters else None,
                    top=100  # Récupérer plus de résultats pour un meilleur scoring
                )
                
                # Convertir les résultats
                for result in azure_results:
                    results.append({
                        'id': result.get('id'),
                        'title': result.get('title', 'Sans titre'),
                        'content': result.get('content', ''),
                        'source': 'Azure Search',
                        'type': result.get('documentType', 'document'),
                        'score': result.get('@search.score', 0) * 10,  # Normaliser le score
                        'metadata': {
                            'date': result.get('date'),
                            'author': result.get('author')
                        }
                    })
        
        except Exception as e:
            print(f"Erreur recherche Azure: {e}")
        
        return results
    
    def _check_document_match(self, doc_id: str, doc: Dict, query_analysis: QueryAnalysis, filters: Optional[Dict]) -> Optional[Dict]:
        """Vérifie si un document correspond aux critères (thread-safe)"""
        
        if not self._document_matches(doc, query_analysis, filters):
            return None
        
        return {
            'id': doc_id,
            'title': doc.get('title', 'Sans titre'),
            'content': doc.get('content', ''),
            'source': doc.get('source', 'Local'),
            'type': doc.get('type', 'document'),
            'metadata': doc.get('metadata', {})
        }
    
    def _document_matches(self, doc: Union[Dict, Document], query_analysis: QueryAnalysis, filters: Optional[Dict] = None) -> bool:
        """Vérification optimisée de correspondance"""
        
        # Obtenir le contenu
        if isinstance(doc, dict):
            content = doc.get('content', '').lower()
            title = doc.get('title', '').lower()
            doc_type = doc.get('type')
        else:
            content = getattr(doc, 'content', '').lower()
            title = getattr(doc, 'title', '').lower()
            doc_type = getattr(doc, 'type', None)
        
        # Vérification rapide des filtres
        if filters:
            if 'document_type' in filters and doc_type != filters['document_type']:
                return False
        
        # Vérification de la référence (prioritaire)
        if query_analysis.reference:
            if query_analysis.reference.lower() in title or query_analysis.reference.lower() in content:
                return True
        
        # Vérification des mots-clés
        if not query_analysis.keywords:
            return False
        
        # Au moins 30% des mots-clés doivent matcher
        matches = sum(1 for keyword in query_analysis.keywords if keyword in content or keyword in title)
        match_ratio = matches / len(query_analysis.keywords)
        
        return match_ratio >= 0.3
    
    def _intelligent_scoring(self, results: List[Dict], query_analysis: QueryAnalysis) -> List[Dict]:
        """Scoring intelligent basé sur multiple critères"""
        
        for result in results:
            score = result.get('score', 0)
            
            content = result.get('content', '').lower()
            title = result.get('title', '').lower()
            
            # Score basé sur la correspondance exacte de la référence
            if query_analysis.reference:
                if query_analysis.reference.lower() in title:
                    score += 20
                if query_analysis.reference.lower() in content:
                    score += 10
            
            # Score basé sur le type de document
            if query_analysis.document_type:
                if query_analysis.document_type.lower() in title:
                    score += 15
            
            # Score pour les mots-clés
            for keyword in query_analysis.keywords:
                # Titre = plus de poids
                score += title.count(keyword) * 3
                # Contenu
                score += min(content.count(keyword), 10) * 1  # Limiter pour éviter le spam
            
            # Score pour les parties mentionnées
            for partie in query_analysis.parties['demandeurs'] + query_analysis.parties['defendeurs']:
                if partie.lower() in title:
                    score += 10
                if partie.lower() in content:
                    score += 5
            
            # Score pour les infractions
            for infraction in query_analysis.infractions:
                if infraction.lower() in content:
                    score += 8
            
            # Bonus pour la fraîcheur (si metadata contient une date)
            if 'date' in result.get('metadata', {}):
                try:
                    doc_date = datetime.fromisoformat(result['metadata']['date'])
                    days_old = (datetime.now() - doc_date).days
                    if days_old < 30:
                        score += 5
                    elif days_old < 90:
                        score += 3
                except:
                    pass
            
            # Pénalité pour les documents trop courts
            if len(content) < 100:
                score *= 0.5
            
            result['score'] = score
        
        return results
    
    def _extract_highlights(self, results: List[Dict], query_analysis: QueryAnalysis) -> List[Dict]:
        """Extrait les passages pertinents pour chaque résultat"""
        
        for result in results:
            content = result.get('content', '')
            highlights = []
            
            # Rechercher les contextes autour des mots-clés
            for keyword in query_analysis.keywords[:5]:  # Limiter aux 5 premiers
                pattern = re.compile(
                    rf'(.{{0,50}}\b{re.escape(keyword)}\b.{{0,50}})',
                    re.IGNORECASE | re.DOTALL
                )
                matches = pattern.findall(content)
                
                for match in matches[:2]:  # Max 2 highlights par mot-clé
                    highlight = match.strip()
                    if highlight and highlight not in highlights:
                        highlights.append(highlight)
            
            # Ajouter un highlight pour la référence si présente
            if query_analysis.reference:
                ref_pattern = re.compile(
                    rf'(.{{0,100}}{re.escape(query_analysis.reference)}.{{0,100}})',
                    re.IGNORECASE | re.DOTALL
                )
                ref_matches = ref_pattern.findall(content)
                for match in ref_matches[:1]:
                    highlights.insert(0, match.strip())
            
            result['highlights'] = highlights[:3]  # Maximum 3 highlights
        
        return results
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Déduplication intelligente basée sur la similarité"""
        
        if not results:
            return []
        
        unique_results = []
        seen_contents = []
        
        for result in results:
            # Créer une signature du document
            title = result.get('title', '')
            content_preview = result.get('content', '')[:200]
            
            # Vérifier la similarité avec les documents déjà vus
            is_duplicate = False
            
            for seen_title, seen_content in seen_contents:
                # Calculer la similarité
                title_similarity = difflib.SequenceMatcher(None, title, seen_title).ratio()
                content_similarity = difflib.SequenceMatcher(None, content_preview, seen_content).ratio()
                
                # Si très similaire, considérer comme duplicata
                if title_similarity > 0.85 or content_similarity > 0.85:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
                seen_contents.append((title, content_preview))
        
        return unique_results
    
    def _create_facets(self, results: List[Dict]) -> Dict[str, Dict[str, int]]:
        """Crée des facettes pour le filtrage dynamique"""
        
        facets = {
            'sources': {},
            'types': {},
            'dates': {},
            'scores': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        for result in results:
            # Facette source
            source = result.get('source', 'Inconnu')
            facets['sources'][source] = facets['sources'].get(source, 0) + 1
            
            # Facette type
            doc_type = result.get('type', 'unknown')
            facets['types'][doc_type] = facets['types'].get(doc_type, 0) + 1
            
            # Facette score
            score = result.get('score', 0)
            if score >= 20:
                facets['scores']['high'] += 1
            elif score >= 10:
                facets['scores']['medium'] += 1
            else:
                facets['scores']['low'] += 1
        
        return facets
    
    def _generate_suggestions(self, query_analysis: QueryAnalysis, results_count: int) -> List[str]:
        """Génère des suggestions de recherche alternatives"""
        
        suggestions = []
        
        # Si peu de résultats, suggérer des recherches plus larges
        if results_count < 5:
            if query_analysis.reference:
                suggestions.append(f"Tous les documents du dossier {query_analysis.reference}")
            
            if query_analysis.infractions:
                suggestions.append(f"Jurisprudence {query_analysis.infractions[0]}")
            
            if query_analysis.keywords:
                # Suggérer sans certains mots-clés
                reduced_keywords = query_analysis.keywords[:-1] if len(query_analysis.keywords) > 1 else []
                if reduced_keywords:
                    suggestions.append(' '.join(reduced_keywords))
        
        # Si beaucoup de résultats, suggérer des affinements
        elif results_count > 50:
            if not query_analysis.document_type:
                suggestions.append(f"{query_analysis.original_query} conclusions")
                suggestions.append(f"{query_analysis.original_query} jugement")
            
            if not query_analysis.reference and query_analysis.parties['demandeurs']:
                suggestions.append(f"@{query_analysis.parties['demandeurs'][0][:8].upper()}")
        
        return suggestions[:3]  # Maximum 3 suggestions
    
    def _convert_to_document(self, result: Dict) -> Document:
        """Convertit un résultat en Document avec highlights"""
        
        doc = Document(
            id=result.get('id', ''),
            title=result.get('title', 'Sans titre'),
            content=result.get('content', ''),
            source=result.get('source', ''),
            metadata={
                'score': result.get('score', 0),
                'type': result.get('type', 'unknown'),
                'date': result.get('metadata', {}).get('date')
            }
        )
        
        # Ajouter les highlights
        doc.highlights = result.get('highlights', [])
        
        return doc
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les recherches effectuées"""
        
        stats = {
            'total_searches': len(self._search_history),
            'cache_size': len(self._cache),
            'recent_searches': self._search_history[-10:],
            'popular_keywords': {},
            'average_results': 0
        }
        
        if self._search_history:
            # Calculer la moyenne des résultats
            total_results = sum(h['results_count'] for h in self._search_history)
            stats['average_results'] = total_results / len(self._search_history)
            
            # Extraire les mots-clés populaires
            all_keywords = []
            for history in self._search_history:
                words = history['query'].lower().split()
                all_keywords.extend([w for w in words if w not in self._common_terms])
            
            # Compter les occurrences
            for keyword in all_keywords:
                stats['popular_keywords'][keyword] = stats['popular_keywords'].get(keyword, 0) + 1
            
            # Garder seulement le top 10
            stats['popular_keywords'] = dict(
                sorted(stats['popular_keywords'].items(), key=lambda x: x[1], reverse=True)[:10]
            )
        
        return stats
    
    def clear_cache(self):
        """Vide le cache de recherche"""
        self._cache.clear()
    
    async def export_search_history(self) -> List[Dict]:
        """Exporte l'historique de recherche"""
        return self._search_history.copy()