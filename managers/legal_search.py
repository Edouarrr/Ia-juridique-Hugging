# managers/legal_search.py
"""
Gestionnaire de recherche juridique multi-sources
Recherche simultanée sur Judilibre, Légifrance et via IA
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
from urllib.parse import quote, urlencode
import streamlit as st

from modules.dataclasses import (
    JurisprudenceReference, 
    JurisprudenceSearch,
    DocumentJuridique,
    SourceJurisprudence,
    TypeJuridiction
)
from managers.multi_llm_manager import MultiLLMManager

logger = logging.getLogger(__name__)

class LegalSearchManager:
    """Gestionnaire unifié de recherche juridique"""
    
    def __init__(self, llm_manager: Optional[MultiLLMManager] = None):
        self.llm_manager = llm_manager or MultiLLMManager()
        self.session = None
        
        # Configuration Judilibre avec clés intégrées
        self.judilibre_config = {
            "enabled": True,
            "base_url": "https://api.piste.gouv.fr/cassation/judilibre/v1",
            "api_key": "ac72ad69-ef21-4af2-b3e2-6fa1132a8348",
            "client_secret": "ec344bdb-c1f0-482c-ac1e-bb9254ae6adb",
            "endpoints": {
                "search": "/search",
                "decision": "/decision",
                "export": "/export"
            }
        }
        
        # Configuration Légifrance avec clés intégrées
        self.legifrance_config = {
            "enabled": True,
            "base_url": "https://api.piste.gouv.fr/dila/legifrance/v1",
            "oauth_url": "https://oauth.piste.gouv.fr/api/oauth/token",
            "client_id": "ac72ad69-ef21-4af2-b3e2-6fa1132a8348",
            "client_secret": "ec344bdb-c1f0-482c-ac1e-bb9254ae6adb",
            "endpoints": {
                "search": "/search",
                "consult": "/consult",
                "download": "/download"
            }
        }
        
        self.legifrance_token = None
        self.token_expiry = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_all_sources(
        self, 
        search_params: JurisprudenceSearch,
        include_ai: bool = True
    ) -> Dict[str, List[DocumentJuridique]]:
        """Recherche sur toutes les sources disponibles"""
        tasks = {}
        
        # Judilibre
        if SourceJurisprudence.JUDILIBRE in search_params.sources and self.judilibre_config['enabled']:
            tasks['judilibre'] = self.search_judilibre(search_params)
            
        # Légifrance
        if SourceJurisprudence.LEGIFRANCE in search_params.sources and self.legifrance_config['enabled']:
            tasks['legifrance'] = self.search_legifrance(search_params)
            
        # IA (si demandé et disponible)
        if include_ai and self.llm_manager and self.llm_manager.clients:
            tasks['ai'] = self.search_with_ai(search_params)
        
        # Exécuter toutes les recherches en parallèle
        results = await asyncio.gather(
            *[task for task in tasks.values()],
            return_exceptions=True
        )
        
        # Organiser les résultats
        search_results = {}
        for i, (source, result) in enumerate(tasks.items()):
            if isinstance(results[i], Exception):
                logger.error(f"Erreur recherche {source}: {results[i]}")
                search_results[source] = []
            else:
                search_results[source] = results[i] or []
                
        return search_results
    
    async def get_legifrance_token(self) -> Optional[str]:
        """Obtient un token OAuth2 pour Légifrance"""
        if self.legifrance_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.legifrance_token
            
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.legifrance_config['client_id'],
            'client_secret': self.legifrance_config['client_secret'],
            'scope': 'openid'
        }
        
        try:
            async with self.session.post(
                self.legifrance_config['oauth_url'],
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.legifrance_token = result['access_token']
                    self.token_expiry = datetime.now() + timedelta(hours=1)
                    return self.legifrance_token
        except Exception as e:
            logger.error(f"Erreur token Légifrance: {e}")
        return None
    
    async def search_judilibre(self, search_params: JurisprudenceSearch) -> List[DocumentJuridique]:
        """Recherche sur Judilibre"""
        headers = {
            'KeyId': self.judilibre_config['api_key'],
            'Accept': 'application/json'
        }
        
        # Construire la requête
        query_terms = []
        
        # Mots-clés
        if search_params.keywords:
            query_terms.extend(search_params.keywords)
            
        # Infractions
        if search_params.infractions:
            query_terms.extend(search_params.infractions)
            
        # Articles
        if search_params.articles:
            query_terms.extend(search_params.articles)
        
        params = {
            'query': ' '.join(query_terms),
            'field': ['numero', 'date_creation', 'sommaire', 'formation', 'solution'],
            'size': search_params.max_results,
            'sort': search_params.sort_by
        }
        
        # Filtres de date
        if search_params.date_debut:
            params['date_start'] = search_params.date_debut.strftime('%Y-%m-%d')
        if search_params.date_fin:
            params['date_end'] = search_params.date_fin.strftime('%Y-%m-%d')
            
        # Filtres de juridiction
        if search_params.juridictions:
            params['juridiction'] = [j.value for j in search_params.juridictions]
        
        try:
            url = f"{self.judilibre_config['base_url']}{self.judilibre_config['endpoints']['search']}"
            async with self.session.get(url, headers=headers, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_judilibre_results(data.get('results', []))
                else:
                    logger.error(f"Erreur Judilibre: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Erreur recherche Judilibre: {e}")
            return []
    
    async def search_legifrance(self, search_params: JurisprudenceSearch) -> List[DocumentJuridique]:
        """Recherche sur Légifrance"""
        token = await self.get_legifrance_token()
        if not token:
            return []
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Construire la requête
        search_terms = []
        if search_params.keywords:
            search_terms.extend(search_params.keywords)
        if search_params.infractions:
            search_terms.extend(search_params.infractions)
        
        search_data = {
            'fond': 'JURI',
            'recherche': {
                'typeRecherche': 'multicriteres',
                'mots': ' '.join(search_terms),
                'champRecherche': 'ALL',
                'operateur': 'ET'
            },
            'facettes': True,
            'nbResultat': search_params.max_results
        }
        
        # Filtres additionnels
        if search_params.date_debut or search_params.date_fin:
            search_data['recherche']['periode'] = {}
            if search_params.date_debut:
                search_data['recherche']['periode']['debut'] = search_params.date_debut.strftime('%Y-%m-%d')
            if search_params.date_fin:
                search_data['recherche']['periode']['fin'] = search_params.date_fin.strftime('%Y-%m-%d')
        
        try:
            url = f"{self.legifrance_config['base_url']}{self.legifrance_config['endpoints']['search']}"
            async with self.session.post(url, headers=headers, json=search_data, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_legifrance_results(data.get('results', []))
                else:
                    logger.error(f"Erreur Légifrance: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Erreur recherche Légifrance: {e}")
            return []
    
    async def search_with_ai(self, search_params: JurisprudenceSearch) -> List[DocumentJuridique]:
        """Recherche via IA avec génération de jurisprudences"""
        if not self.llm_manager or not self.llm_manager.clients:
            return []
            
        # Construire le prompt
        prompt = f"""Recherche de jurisprudences pertinentes :
        
Mots-clés : {', '.join(search_params.keywords)}
Infractions : {', '.join(search_params.infractions) if search_params.infractions else 'Toutes'}
Articles : {', '.join(search_params.articles) if search_params.articles else 'Tous'}

Fournis une liste de jurisprudences pertinentes avec pour chaque décision :
- Juridiction, date et numéro exact
- Principe retenu
- Mots-clés
- Pertinence pour cette recherche

Format attendu : Une jurisprudence par paragraphe avec tous les éléments."""

        try:
            # Utiliser le premier LLM disponible
            provider = list(self.llm_manager.clients.keys())[0]
            
            response = await self.llm_manager.query_single_llm(
                provider,
                prompt,
                "Tu es un expert en recherche juridique française."
            )
            
            if response['success']:
                return self._parse_ai_results(response['response'], search_params)
            else:
                return []
        except Exception as e:
            logger.error(f"Erreur recherche IA: {e}")
            return []
    
    def _parse_judilibre_results(self, results: List[Dict]) -> List[DocumentJuridique]:
        """Parse les résultats Judilibre"""
        documents = []
        
        for result in results:
            try:
                # Créer la référence
                ref = JurisprudenceReference(
                    juridiction=result.get('juridiction', 'Cass.'),
                    date=result.get('date_creation', ''),
                    numero=result.get('numero', ''),
                    sommaire=result.get('sommaire'),
                    url_source=f"https://www.courdecassation.fr/decision/{result['id']}",
                    verified=True,
                    found_on=['judilibre']
                )
                
                # Créer le document
                doc = DocumentJuridique(
                    id=result.get('id', ''),
                    titre=ref.to_citation(),
                    type_document='jurisprudence',
                    contenu=result.get('sommaire', ''),
                    date_document=datetime.now(),
                    source='Judilibre',
                    url=ref.url_source,
                    mots_cles=result.get('themes', []),
                    pertinence=result.get('score', 0.8),
                    reference=ref
                )
                
                documents.append(doc)
                
            except Exception as e:
                logger.warning(f"Erreur parsing résultat Judilibre: {e}")
                
        return documents
    
    def _parse_legifrance_results(self, results: List[Dict]) -> List[DocumentJuridique]:
        """Parse les résultats Légifrance"""
        documents = []
        
        for result in results:
            try:
                # Extraire les informations
                titre = result.get('titre', '')
                
                # Créer la référence
                ref = JurisprudenceReference(
                    juridiction=self._extract_juridiction_from_title(titre),
                    date=result.get('dateDecision', ''),
                    numero=self._extract_numero_from_title(titre),
                    sommaire=result.get('sommaire'),
                    url_source=f"https://www.legifrance.gouv.fr/juri/id/{result['id']}",
                    verified=True,
                    found_on=['legifrance']
                )
                
                # Créer le document
                doc = DocumentJuridique(
                    id=result.get('id', ''),
                    titre=titre,
                    type_document='jurisprudence',
                    contenu=result.get('texte', result.get('sommaire', '')),
                    date_document=datetime.now(),
                    source='Légifrance',
                    url=ref.url_source,
                    mots_cles=result.get('mots_cles', []),
                    pertinence=result.get('pertinence', 0.8),
                    reference=ref
                )
                
                documents.append(doc)
                
            except Exception as e:
                logger.warning(f"Erreur parsing résultat Légifrance: {e}")
                
        return documents
    
    def _parse_ai_results(self, response: str, search_params: JurisprudenceSearch) -> List[DocumentJuridique]:
        """Parse les résultats générés par l'IA"""
        documents = []
        
        # Extraire les jurisprudences du texte
        from managers.jurisprudence_verifier import JurisprudenceVerifier
        verifier = JurisprudenceVerifier()
        references = verifier.extract_references_from_text(response)
        
        # Créer un document pour chaque référence
        for i, ref in enumerate(references):
            # Marquer comme proposée par l'IA
            ref.ai_proposed = True
            ref.verified = False
            
            doc = DocumentJuridique(
                id=f"ai_{i}_{datetime.now().timestamp()}",
                titre=ref.to_citation(),
                type_document='jurisprudence',
                contenu=self._extract_principle_for_reference(response, ref),
                date_document=datetime.now(),
                source='IA',
                url=None,
                mots_cles=search_params.keywords,
                pertinence=0.7,  # Score par défaut pour l'IA
                reference=ref
            )
            
            documents.append(doc)
            
        return documents
    
    def _extract_juridiction_from_title(self, title: str) -> str:
        """Extrait la juridiction du titre Légifrance"""
        # Patterns courants
        if 'Cour de cassation' in title:
            if 'criminelle' in title:
                return 'Cass. crim.'
            elif 'civile' in title:
                return 'Cass. civ.'
            elif 'commerciale' in title:
                return 'Cass. com.'
            elif 'sociale' in title:
                return 'Cass. soc.'
            return 'Cass.'
        elif 'Conseil d\'État' in title:
            return 'CE'
        elif 'Cour d\'appel' in title:
            return 'CA'
        return 'Juridiction'
    
    def _extract_numero_from_title(self, title: str) -> str:
        """Extrait le numéro du titre"""
        import re
        match = re.search(r'n°\s*([\d\-\.]+)', title)
        if match:
            return match.group(1)
        return ''
    
    def _extract_principle_for_reference(self, text: str, ref: JurisprudenceReference) -> str:
        """Extrait le principe énoncé pour une référence"""
        # Rechercher le contexte autour de la citation
        citation = ref.to_citation()
        index = text.find(citation)
        
        if index != -1:
            # Extraire le paragraphe contenant la citation
            start = max(0, text.rfind('\n', 0, index))
            end = text.find('\n', index + len(citation))
            if end == -1:
                end = len(text)
            return text[start:end].strip()
        return "Principe à vérifier"
    
    def merge_and_deduplicate_results(
        self, 
        results: Dict[str, List[DocumentJuridique]]
    ) -> List[DocumentJuridique]:
        """Fusionne et déduplique les résultats de toutes les sources"""
        all_documents = []
        seen_references = set()
        
        # Priorité : Judilibre > Légifrance > IA
        priority_order = ['judilibre', 'legifrance', 'ai']
        
        for source in priority_order:
            if source in results:
                for doc in results[source]:
                    if hasattr(doc, 'reference') and doc.reference:
                        ref_key = f"{doc.reference.juridiction}_{doc.reference.numero}"
                        if ref_key not in seen_references:
                            seen_references.add(ref_key)
                            all_documents.append(doc)
                    else:
                        # Document sans référence (rare)
                        all_documents.append(doc)
        
        # Trier par pertinence
        all_documents.sort(key=lambda x: x.pertinence, reverse=True)
        
        return all_documents


# Fonction d'intégration Streamlit
def display_legal_search_interface():
    """Interface de recherche juridique intégrée"""
    st.markdown("### 🔍 Recherche de jurisprudence multi-sources")
    
    # Initialiser le gestionnaire si nécessaire
    if 'legal_search_manager' not in st.session_state:
        st.session_state.legal_search_manager = LegalSearchManager()
    
    # Paramètres de recherche
    col1, col2 = st.columns(2)
    
    with col1:
        keywords = st.text_input(
            "Mots-clés",
            placeholder="Ex: abus biens sociaux dirigeant",
            key="legal_search_keywords"
        )
        
        infractions = st.multiselect(
            "Types d'infractions",
            options=[
                "Abus de biens sociaux",
                "Corruption",
                "Blanchiment",
                "Escroquerie",
                "Délit d'initié",
                "Fraude fiscale",
                "Trafic d'influence",
                "Prise illégale d'intérêts"
            ],
            key="legal_search_infractions"
        )
        
    with col2:
        juridictions = st.multiselect(
            "Juridictions",
            options=[
                TypeJuridiction.CASS_CRIM,
                TypeJuridiction.CASS_COM,
                TypeJuridiction.CASS_CIV,
                TypeJuridiction.CASS_SOC,
                TypeJuridiction.CE,
                TypeJuridiction.CA
            ],
            format_func=lambda x: x.value,
            key="legal_search_juridictions"
        )
        
        date_range = st.date_input(
            "Période",
            value=[],
            help="Laisser vide pour toutes les dates",
            key="legal_search_dates"
        )
    
    # Options avancées
    with st.expander("⚙️ Options avancées"):
        col3, col4 = st.columns(2)
        
        with col3:
            sources_map = {
                "Judilibre": SourceJurisprudence.JUDILIBRE,
                "Légifrance": SourceJurisprudence.LEGIFRANCE
            }
            
            selected_sources_names = st.multiselect(
                "Sources",
                options=list(sources_map.keys()),
                default=list(sources_map.keys()),
                key="legal_search_sources"
            )
            
            sources = [sources_map[name] for name in selected_sources_names]
            
        with col4:
            max_results = st.slider(
                "Nombre de résultats",
                min_value=10,
                max_value=100,
                value=30,
                key="legal_search_max_results"
            )
            
        include_ai = st.checkbox(
            "Inclure les suggestions IA",
            value=True,
            help="L'IA peut proposer des jurisprudences qui seront vérifiées",
            key="legal_search_include_ai"
        )
    
    # Bouton de recherche
    if st.button("🔎 Rechercher", type="primary", key="legal_search_button"):
        if not keywords and not infractions:
            st.error("Veuillez saisir au moins un mot-clé ou sélectionner une infraction")
            return
            
        # Créer les paramètres de recherche
        search_params = JurisprudenceSearch(
            keywords=keywords.split() if keywords else [],
            infractions=infractions,
            juridictions=juridictions,
            date_debut=date_range[0] if len(date_range) == 2 else None,
            date_fin=date_range[1] if len(date_range) == 2 else None,
            sources=sources,
            max_results=max_results
        )
        
        # Effectuer la recherche
        with st.spinner("🔄 Recherche en cours sur les bases juridiques..."):
            # Exécuter la recherche asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def run_search():
                async with st.session_state.legal_search_manager as manager:
                    return await manager.search_all_sources(search_params, include_ai)
            
            results = loop.run_until_complete(run_search())
            
            # Stocker les résultats
            st.session_state.legal_search_results = results
        
        # Afficher les résultats
        display_search_results(results)

def display_search_results(results: Dict[str, List[DocumentJuridique]]):
    """Affiche les résultats de recherche"""
    # Fusionner et dédupliquer
    manager = st.session_state.legal_search_manager
    all_results = manager.merge_and_deduplicate_results(results)
    
    # Compter les résultats
    total = len(all_results)
    counts = {source: len(docs) for source, docs in results.items()}
    
    st.success(f"✅ Recherche terminée : {total} résultats uniques")
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Judilibre", counts.get('judilibre', 0))
    with col3:
        st.metric("Légifrance", counts.get('legifrance', 0))
    with col4:
        st.metric("IA", counts.get('ai', 0))
    
    # Tabs pour les résultats
    tabs = st.tabs(["🔍 Tous", "⚖️ Judilibre", "📚 Légifrance", "🤖 IA"])
    
    with tabs[0]:
        st.markdown("#### Résultats consolidés (sans doublons)")
        display_documents_list(all_results)
        
    with tabs[1]:
        st.markdown("#### Résultats Judilibre")
        if 'judilibre' in results:
            display_documents_list(results['judilibre'])
        else:
            st.info("Aucun résultat Judilibre")
            
    with tabs[2]:
        st.markdown("#### Résultats Légifrance")
        if 'legifrance' in results:
            display_documents_list(results['legifrance'])
        else:
            st.info("Aucun résultat Légifrance")
            
    with tabs[3]:
        st.markdown("#### Suggestions IA (à vérifier)")
        if 'ai' in results:
            st.warning("⚠️ Ces jurisprudences sont suggérées par l'IA et doivent être vérifiées")
            display_documents_list(results['ai'])
        else:
            st.info("Aucune suggestion IA")

def display_documents_list(documents: List[DocumentJuridique]):
    """Affiche une liste de documents juridiques"""
    for doc in documents:
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Titre avec indicateur de vérification
                if hasattr(doc, 'reference') and doc.reference:
                    if doc.reference.verified:
                        st.markdown(f"✅ **{doc.titre}**")
                    else:
                        st.markdown(f"⚠️ **{doc.titre}** *(à vérifier)*")
                else:
                    st.markdown(f"**{doc.titre}**")
                
                # Contenu
                if doc.contenu:
                    st.caption(doc.contenu[:300] + "..." if len(doc.contenu) > 300 else doc.contenu)
                
                # Métadonnées
                meta_parts = []
                if doc.source:
                    meta_parts.append(f"Source: {doc.source}")
                if doc.pertinence:
                    meta_parts.append(f"Pertinence: {doc.pertinence:.0%}")
                if doc.mots_cles:
                    meta_parts.append(f"Mots-clés: {', '.join(doc.mots_cles[:3])}")
                
                st.caption(" | ".join(meta_parts))
            
            with col2:
                if doc.url:
                    st.link_button("📄 Consulter", doc.url)
                
                # Bouton pour ajouter aux documents
                if st.button("➕", key=f"add_juris_{doc.id}", help="Ajouter aux documents"):
                    add_jurisprudence_to_documents(doc)
            
            st.markdown("---")

def add_jurisprudence_to_documents(doc: DocumentJuridique):
    """Ajoute une jurisprudence aux documents de l'affaire"""
    from models.dataclasses import Document
    
    # Créer un document à partir de la jurisprudence
    new_doc = Document(
        id=f"juris_{doc.id}",
        title=doc.titre,
        content=f"{doc.titre}\n\n{doc.contenu}",
        source=f"Jurisprudence - {doc.source}",
        metadata={
            'type': 'jurisprudence',
            'source': doc.source,
            'url': doc.url,
            'verified': doc.reference.verified if hasattr(doc, 'reference') and doc.reference else False
        }
    )
    
    # Ajouter aux documents
    st.session_state.azure_documents[new_doc.id] = new_doc
    st.success(f"✅ Jurisprudence ajoutée aux documents")


# Export
__all__ = ['LegalSearchManager', 'display_legal_search_interface']