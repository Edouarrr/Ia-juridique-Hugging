"""Service de recherche universelle pour l'application"""

import asyncio
import difflib
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import streamlit as st

# ========================= CLASSES DE DONNÉES =========================

@dataclass
class Partie:
    """Classe représentant une partie dans un dossier"""
    id: str
    nom: str
    type_partie: str
    type_personne: str
    phase_procedure: Any
    info_entreprise: Optional[Dict] = None

@dataclass 
class Document:
    """Classe représentant un document"""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)

@dataclass
class QueryAnalysis:
    """Analyse détaillée d'une requête de recherche"""
    original_query: str
    query_lower: str
    timestamp: datetime
    reference: Optional[str] = None
    document_type: Optional[str] = None
    action: Optional[str] = None
    subject_matter: Optional[str] = None
    phase_procedurale: Optional[str] = None
    parties: Dict[str, List[str]] = field(default_factory=lambda: {'demandeurs': [], 'defendeurs': []})
    infractions: List[str] = field(default_factory=list)
    style_request: Optional[str] = None
    date_filter: Optional[Tuple[datetime, datetime]] = None
    keywords: List[str] = field(default_factory=list)
    search_type: str = 'general'  # general, dossier, jurisprudence, partie
    command_type: Optional[str] = None  # Pour le routing

@dataclass
class SearchResult:
    """Résultat de recherche enrichi"""
    documents: List[Document]
    query: str
    total_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

# ========================= SERVICE PRINCIPAL =========================

class UniversalSearchService:
    """Service unifié pour toutes les recherches dans l'application"""
    
    # Patterns centralisés
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
        """Initialisation du service"""
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
        Recherche universelle optimisée
        
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
            if (datetime.now() - cached_result.timestamp).seconds < 300:
                return cached_result
        
        # Analyser la requête
        query_analysis = self.analyze_query_advanced(query)

        # Enrichir avec le résumé du dossier si disponible
        contextual_prompt = query
        if query_analysis.reference:
            doc_manager = st.session_state.get('doc_manager')
            summary = None
            if doc_manager and hasattr(doc_manager, 'get_summary'):
                try:
                    summary = doc_manager.get_summary(query_analysis.reference)
                except Exception:
                    summary = None
            if summary:
                contextual_prompt = (
                    f"Contexte du dossier :\n{summary}\n\nQuestion : {query}"
                )
                # Réanalyser la requête avec le contexte
                query_analysis = self.analyze_query_advanced(contextual_prompt)

        # Recherche sur tous les dossiers si la requête le demande
        if (
            not query_analysis.reference
            and re.search(r"\b(tous|ensemble)\b", query_analysis.query_lower)
            and "@" not in query
            and "#" not in query
        ):
            return await self.search_all_dossiers(query)
        
        # Recherches parallèles
        search_tasks = []
        
        # Recherche locale
        local_task = self._search_local_documents(query_analysis, filters)
        search_tasks.append(local_task)
        
        # Recherche Azure si disponible
        if 'azure_search_manager' in st.session_state:
            azure_task = self._search_azure_documents(query_analysis, filters)
            search_tasks.append(azure_task)
        
        # Recherche dans l'historique si référence @
        if query_analysis.reference:
            history_task = self._search_reference_history(query_analysis.reference)
            search_tasks.append(history_task)
        
        # Exécuter toutes les recherches
        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Combiner les résultats
        combined_results = []
        for result in all_results:
            if isinstance(result, list):
                combined_results.extend(result)
        
        # Traitement des résultats
        unique_results = self._deduplicate_results(combined_results)
        scored_results = self._intelligent_scoring(unique_results, query_analysis)
        highlighted_results = self._extract_highlights(scored_results, query_analysis)
        
        # Tri et limitation
        sorted_results = sorted(highlighted_results, key=lambda x: x.get('score', 0), reverse=True)
        top_results = sorted_results[:50]
        documents = [self._convert_to_document(r) for r in top_results]
        
        # Créer le résultat
        result = SearchResult(
            documents=documents,
            query=query,
            total_count=len(sorted_results),
            facets=self._create_facets(sorted_results),
            suggestions=self._generate_suggestions(query_analysis, len(sorted_results))
        )
        
        # Mettre en cache
        self._cache[cache_key] = result
        
        # Historique
        self._search_history.append({
            'query': query,
            'timestamp': datetime.now(),
            'results_count': len(sorted_results)
        })
        
        return result
    
    def analyze_query_advanced(self, query: str) -> QueryAnalysis:
        """Analyse avancée de la requête"""
        analysis = QueryAnalysis(
            original_query=query,
            query_lower=query.lower(),
            timestamp=datetime.now()
        )
        
        # Détection du type de commande
        self._detect_command_type(analysis)
        
        # Extraction de la référence
        ref_patterns = [
            r'@([A-Za-z0-9_\-]+)',
            r'dossier\s+([A-Za-z0-9_\-]+)',
            r'affaire\s+([A-Za-z0-9_\-]+)',
        ]
        
        for pattern in ref_patterns:
            ref_match = re.search(pattern, query, re.IGNORECASE)
            if ref_match:
                analysis.reference = ref_match.group(1).upper()
                analysis.search_type = 'dossier'
                st.session_state.selected_folder = analysis.reference
                break
        
        # Type de document
        for pattern, doc_type in self.DOCUMENT_TYPES.items():
            if re.search(pattern, analysis.query_lower):
                analysis.document_type = doc_type
                break
        
        # Parties et infractions
        analysis.parties = self._extract_parties_advanced(query)
        analysis.infractions = self._extract_infractions_advanced(query)
        
        # Mots-clés
        analysis.keywords = self._extract_keywords(query)
        
        # Type de recherche
        if 'jurisprudence' in analysis.query_lower:
            analysis.search_type = 'jurisprudence'
        elif analysis.parties['demandeurs'] or analysis.parties['defendeurs']:
            analysis.search_type = 'partie'
        
        return analysis
    
    def _detect_command_type(self, analysis: QueryAnalysis):
        """Détecte le type de commande"""
        query_lower = analysis.query_lower
        
        command_mappings = {
            'redaction': ['rédige', 'rédiger', 'écrire', 'créer'],
            'plainte': ['plainte'],
            'plaidoirie': ['plaidoirie', 'plaider', 'audience'],
            'preparation_client': ['préparer client', 'préparation', 'coaching'],
            'import': ['import', 'importer', 'charger', 'upload'],
            'export': ['export', 'exporter', 'télécharger', 'download'],
            'email': ['email', 'envoyer', 'mail', 'courrier électronique'],
            'analysis': ['analyser', 'analyse', 'étudier', 'examiner'],
            'piece_selection': ['sélectionner pièces', 'pièces', 'sélection'],
            'bordereau': ['bordereau'],
            'synthesis': ['synthèse', 'synthétiser', 'résumer'],
            'template': ['template', 'modèle', 'gabarit'],
            'jurisprudence': ['jurisprudence', 'juris', 'décision', 'arrêt'],
            'timeline': ['chronologie', 'timeline', 'frise'],
            'mapping': ['cartographie', 'mapping', 'carte', 'réseau'],
            'comparison': ['comparer', 'comparaison', 'différences']
        }
        
        for cmd_type, keywords in command_mappings.items():
            if any(word in query_lower for word in keywords):
                analysis.command_type = cmd_type
                break
        else:
            analysis.command_type = 'search'
    
    def extract_parties_from_query(self, query: str) -> Dict[str, List[str]]:
        """Méthode publique pour extraire les parties"""
        return self._extract_parties_advanced(query)
    
    def extract_infractions_from_query(self, query: str) -> List[str]:
        """Méthode publique pour extraire les infractions"""
        return self._extract_infractions_advanced(query)
    
    def _extract_parties_advanced(self, query: str) -> Dict[str, List[str]]:
        """Extraction des parties avec patterns multiples"""
        parties = {'demandeurs': [], 'defendeurs': []}
        query_lower = query.lower()
        
        # Méthode 1: Structure "pour X contre Y"
        if ' pour ' in query_lower and ' contre ' in query_lower:
            partie_pour = query_lower.split(' pour ')[1].split(' contre ')[0]
            partie_contre = query_lower.split(' contre ')[1]
            
            # Chercher demandeurs
            for keyword, nom_formate in self.DEMANDEURS_PATTERNS:
                if keyword in partie_pour:
                    parties['demandeurs'].append(nom_formate)
            
            # Chercher défendeurs
            for keyword, nom_formate in self.DEFENDEURS_PATTERNS:
                if keyword in partie_contre:
                    parties['defendeurs'].append(nom_formate)
        
        # Méthode 2: Recherche globale
        else:
            # Défendeurs d'abord (souvent après "contre")
            if ' contre ' in query_lower:
                partie_contre = query_lower.split(' contre ')[1]
                for keyword, nom_formate in self.DEFENDEURS_PATTERNS:
                    if keyword in partie_contre:
                        parties['defendeurs'].append(nom_formate)
            
            # Puis demandeurs
            for keyword, nom_formate in self.DEMANDEURS_PATTERNS:
                if keyword in query_lower and nom_formate not in parties['defendeurs']:
                    if ' contre ' not in query_lower or keyword not in query_lower.split(' contre ')[1]:
                        parties['demandeurs'].append(nom_formate)
        
        # Patterns alternatifs
        patterns = [
            (r'(.+?)\s+c(?:ontre)?\.?\s+(.+)', 'versus'),
            (r'(.+?)\s+vs?\.?\s+(.+)', 'versus'),
            (r'demandeur[s]?\s*:\s*(.+?)(?:\s*défendeur|$)', 'demandeur'),
            (r'défendeur[s]?\s*:\s*(.+?)(?:\s*demandeur|$)', 'defendeur'),
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if pattern_type == 'versus':
                    demandeur_text = match.group(1).strip()
                    defendeur_text = match.group(2).strip()
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
        """Extrait les noms d'entités"""
        entities = []
        
        entity_patterns = [
            r'\b(VINCI|SOGEPROM|BOUYGUES|EIFFAGE)\b',
            r'\b(M\.|Mme|Mr|Monsieur|Madame)\s+([A-Z][A-Za-z]+)\b',
            r'\b(SAS|SARL|SA|SCI|EURL)\s+([A-Z][A-Za-z\s]+?)(?:\s|$)',
            r'\b([A-Z][A-Z\s&]+?)(?:\s+(?:contre|c\.|vs?\.)|$)',
        ]
        
        for pattern in entity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = match.group(0).strip()
                if len(entity) > 2 and entity not in self._common_terms:
                    entities.append(entity)
        
        return entities
    
    def _extract_infractions_advanced(self, query: str) -> List[str]:
        """Extraction des infractions"""
        query_lower = query.lower()
        infractions = []
        
        for keyword, infraction in self.INFRACTIONS_MAP.items():
            if keyword in query_lower and infraction not in infractions:
                infractions.append(infraction)
        
        return infractions
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extrait les mots-clés significatifs"""
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = []
        
        for word in words:
            if (len(word) > 2 and 
                word not in self._common_terms and 
                not word.isdigit()):
                keywords.append(word)
        
        return keywords
    
    async def _search_reference_history(self, reference: str) -> List[Dict]:
        """Recherche dans l'historique des documents"""
        results = []
        
        # Rechercher dans tous les documents stockés
        all_docs = {}
        all_docs.update(st.session_state.get('azure_documents', {}))
        all_docs.update(st.session_state.get('imported_documents', {}))
        
        for doc_id, doc in all_docs.items():
            if reference.lower() in doc.get('title', '').lower() or \
               reference.lower() in doc.get('content', '').lower():
                results.append({
                    'id': doc_id,
                    'title': doc.get('title', 'Sans titre'),
                    'content': doc.get('content', ''),
                    'source': f"Dossier {reference}",
                    'type': 'reference_match',
                    'score': 10
                })
        
        return results
    
    async def _search_local_documents(self, query_analysis: QueryAnalysis, filters: Optional[Dict] = None) -> List[Dict]:
        """Recherche dans les documents locaux"""
        results = []
        
        # Collecter tous les documents
        all_documents = {}
        all_documents.update(st.session_state.get('azure_documents', {}))
        all_documents.update(st.session_state.get('imported_documents', {}))
        
        # Recherche parallèle
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for doc_id, doc in all_documents.items():
                future = executor.submit(
                    self._check_document_match,
                    doc_id, doc, query_analysis, filters
                )
                futures.append(future)
            
            for future in futures:
                match_result = future.result()
                if match_result:
                    results.append(match_result)
        
        return results
    
    async def _search_azure_documents(self, query_analysis: QueryAnalysis, filters: Optional[Dict] = None) -> List[Dict]:
        """Recherche Azure"""
        results = []
        
        search_manager = st.session_state.get('azure_search_manager')
        if not search_manager or not hasattr(search_manager, 'search'):
            return results
        
        try:
            # Construire la requête Azure
            search_terms = []
            
            if query_analysis.reference:
                search_terms.append(query_analysis.reference)
            
            search_terms.extend(query_analysis.keywords[:5])
            
            for partie in query_analysis.parties['demandeurs'][:2] + query_analysis.parties['defendeurs'][:2]:
                search_terms.append(partie)
            
            azure_query = ' '.join(search_terms)
            
            # Filtres Azure
            azure_filters = []
            if filters:
                if 'document_type' in filters:
                    azure_filters.append(f"documentType eq '{filters['document_type']}'")
                if 'date_range' in filters and len(filters['date_range']) == 2:
                    start_date = filters['date_range'][0].isoformat()
                    end_date = filters['date_range'][1].isoformat()
                    azure_filters.append(f"date ge {start_date} and date le {end_date}")
            
            # Recherche
            azure_results = await search_manager.search(
                azure_query,
                filter_string=' and '.join(azure_filters) if azure_filters else None,
                top=100
            )
            
            # Convertir les résultats
            for result in azure_results:
                results.append({
                    'id': result.get('id'),
                    'title': result.get('title', 'Sans titre'),
                    'content': result.get('content', ''),
                    'source': 'Azure Search',
                    'type': result.get('documentType', 'document'),
                    'score': result.get('@search.score', 0) * 10,
                    'metadata': {
                        'date': result.get('date'),
                        'author': result.get('author')
                    }
                })
        
        except Exception as e:
            print(f"Erreur recherche Azure: {e}")
        
        return results
    
    def _check_document_match(self, doc_id: str, doc: Dict, query_analysis: QueryAnalysis, filters: Optional[Dict]) -> Optional[Dict]:
        """Vérifie si un document correspond"""
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
        """Vérification de correspondance"""
        # Obtenir le contenu
        if isinstance(doc, dict):
            content = doc.get('content', '').lower()
            title = doc.get('title', '').lower()
            doc_type = doc.get('type')
        else:
            content = getattr(doc, 'content', '').lower()
            title = getattr(doc, 'title', '').lower()
            doc_type = getattr(doc, 'type', None)
        
        # Filtres
        if filters and 'document_type' in filters and doc_type != filters['document_type']:
            return False
        
        # Référence
        if query_analysis.reference:
            if query_analysis.reference.lower() in title or query_analysis.reference.lower() in content:
                return True
        
        # Mots-clés
        if not query_analysis.keywords:
            return False
        
        matches = sum(1 for keyword in query_analysis.keywords if keyword in content or keyword in title)
        match_ratio = matches / len(query_analysis.keywords)
        
        return match_ratio >= 0.3
    
    def _intelligent_scoring(self, results: List[Dict], query_analysis: QueryAnalysis) -> List[Dict]:
        """Scoring intelligent"""
        for result in results:
            score = result.get('score', 0)
            
            content = result.get('content', '').lower()
            title = result.get('title', '').lower()
            
            # Score référence
            if query_analysis.reference:
                if query_analysis.reference.lower() in title:
                    score += 20
                if query_analysis.reference.lower() in content:
                    score += 10
            
            # Score type document
            if query_analysis.document_type:
                if query_analysis.document_type.lower() in title:
                    score += 15
            
            # Score mots-clés
            for keyword in query_analysis.keywords:
                score += title.count(keyword) * 3
                score += min(content.count(keyword), 10) * 1
            
            # Score parties
            for partie in query_analysis.parties['demandeurs'] + query_analysis.parties['defendeurs']:
                if partie.lower() in title:
                    score += 10
                if partie.lower() in content:
                    score += 5
            
            # Score infractions
            for infraction in query_analysis.infractions:
                if infraction.lower() in content:
                    score += 8
            
            # Bonus fraîcheur
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
            
            # Pénalité documents courts
            if len(content) < 100:
                score *= 0.5
            
            result['score'] = score
        
        return results
    
    def _extract_highlights(self, results: List[Dict], query_analysis: QueryAnalysis) -> List[Dict]:
        """Extrait les passages pertinents"""
        for result in results:
            content = result.get('content', '')
            highlights = []
            
            # Contextes autour des mots-clés
            for keyword in query_analysis.keywords[:5]:
                pattern = re.compile(
                    rf'(.{{0,50}}\b{re.escape(keyword)}\b.{{0,50}})',
                    re.IGNORECASE | re.DOTALL
                )
                matches = pattern.findall(content)
                
                for match in matches[:2]:
                    highlight = match.strip()
                    if highlight and highlight not in highlights:
                        highlights.append(highlight)
            
            # Highlight pour la référence
            if query_analysis.reference:
                ref_pattern = re.compile(
                    rf'(.{{0,100}}{re.escape(query_analysis.reference)}.{{0,100}})',
                    re.IGNORECASE | re.DOTALL
                )
                ref_matches = ref_pattern.findall(content)
                for match in ref_matches[:1]:
                    highlights.insert(0, match.strip())
            
            result['highlights'] = highlights[:3]
        
        return results
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Déduplication intelligente"""
        if not results:
            return []
        
        unique_results = []
        seen_contents = []
        
        for result in results:
            title = result.get('title', '')
            content_preview = result.get('content', '')[:200]
            
            is_duplicate = False
            
            for seen_title, seen_content in seen_contents:
                title_similarity = difflib.SequenceMatcher(None, title, seen_title).ratio()
                content_similarity = difflib.SequenceMatcher(None, content_preview, seen_content).ratio()
                
                if title_similarity > 0.85 or content_similarity > 0.85:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
                seen_contents.append((title, content_preview))
        
        return unique_results
    
    def _create_facets(self, results: List[Dict]) -> Dict[str, Dict[str, int]]:
        """Crée des facettes pour le filtrage"""
        facets = {
            'sources': {},
            'types': {},
            'dates': {},
            'scores': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        for result in results:
            # Source
            source = result.get('source', 'Inconnu')
            facets['sources'][source] = facets['sources'].get(source, 0) + 1
            
            # Type
            doc_type = result.get('type', 'unknown')
            facets['types'][doc_type] = facets['types'].get(doc_type, 0) + 1
            
            # Score
            score = result.get('score', 0)
            if score >= 20:
                facets['scores']['high'] += 1
            elif score >= 10:
                facets['scores']['medium'] += 1
            else:
                facets['scores']['low'] += 1
        
        return facets
    
    def _generate_suggestions(self, query_analysis: QueryAnalysis, results_count: int) -> List[str]:
        """Génère des suggestions"""
        suggestions = []
        
        # Peu de résultats
        if results_count < 5:
            if query_analysis.reference:
                suggestions.append(f"Tous les documents du dossier {query_analysis.reference}")
            
            if query_analysis.infractions:
                suggestions.append(f"Jurisprudence {query_analysis.infractions[0]}")
            
            if query_analysis.keywords and len(query_analysis.keywords) > 1:
                reduced = query_analysis.keywords[:-1]
                suggestions.append(' '.join(reduced))
        
        # Beaucoup de résultats
        elif results_count > 50:
            if not query_analysis.document_type:
                suggestions.append(f"{query_analysis.original_query} conclusions")
                suggestions.append(f"{query_analysis.original_query} jugement")
            
            if not query_analysis.reference and query_analysis.parties['demandeurs']:
                suggestions.append(f"@{query_analysis.parties['demandeurs'][0][:8].upper()}")
        
        return suggestions[:3]
    
    def _convert_to_document(self, result: Dict) -> Document:
        """Convertit un résultat en Document"""
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
        
        doc.highlights = result.get('highlights', [])

        return doc

    async def search_all_dossiers(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, SearchResult]:
        """Recherche la requête sur l'ensemble des dossiers connus."""
        query_analysis = self.analyze_query_advanced(query)

        search_tasks = [self._search_local_documents(query_analysis, filters)]
        if 'azure_search_manager' in st.session_state:
            search_tasks.append(self._search_azure_documents(query_analysis, filters))

        all_results = []
        for result in await asyncio.gather(*search_tasks, return_exceptions=True):
            if isinstance(result, list):
                all_results.extend(result)

        grouped: Dict[str, List[Dict]] = {}
        for res in all_results:
            dossier = (
                res.get('metadata', {}).get('dossier')
                or res.get('metadata', {}).get('reference')
                or str(res.get('id', '')).split('_')[0]
            )
            grouped.setdefault(dossier, []).append(res)

        final_results: Dict[str, SearchResult] = {}
        for dossier, docs in grouped.items():
            unique = self._deduplicate_results(docs)
            scored = self._intelligent_scoring(unique, query_analysis)
            highlighted = self._extract_highlights(scored, query_analysis)
            sorted_docs = sorted(highlighted, key=lambda x: x.get('score', 0), reverse=True)
            documents = [self._convert_to_document(r) for r in sorted_docs]
            final_results[dossier] = SearchResult(
                documents=documents,
                query=query,
                total_count=len(sorted_docs),
                facets=self._create_facets(sorted_docs),
                suggestions=self._generate_suggestions(query_analysis, len(sorted_docs)),
            )

        return final_results
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """Statistiques de recherche"""
        stats = {
            'total_searches': len(self._search_history),
            'cache_size': len(self._cache),
            'recent_searches': self._search_history[-10:],
            'popular_keywords': {},
            'average_results': 0
        }
        
        if self._search_history:
            total_results = sum(h['results_count'] for h in self._search_history)
            stats['average_results'] = total_results / len(self._search_history)
            
            all_keywords = []
            for history in self._search_history:
                words = history['query'].lower().split()
                all_keywords.extend([w for w in words if w not in self._common_terms])
            
            for keyword in all_keywords:
                stats['popular_keywords'][keyword] = stats['popular_keywords'].get(keyword, 0) + 1
            
            stats['popular_keywords'] = dict(
                sorted(stats['popular_keywords'].items(), key=lambda x: x[1], reverse=True)[:10]
            )
        
        return stats
    
    def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
    
    async def export_search_history(self) -> List[Dict]:
        """Exporte l'historique"""
        return self._search_history.copy()

# Singleton
_universal_search_service = None

def get_universal_search_service() -> UniversalSearchService:
    """Retourne l'instance singleton"""
    global _universal_search_service
    if _universal_search_service is None:
        _universal_search_service = UniversalSearchService()
    return _universal_search_service