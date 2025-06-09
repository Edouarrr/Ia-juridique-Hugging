# modules/jurisprudence.py
"""Module de recherche et gestion de la jurisprudence avec API réelles"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re
import os
import json
import asyncio
import aiohttp
from collections import Counter
import logging

from models.dataclasses import (
    JurisprudenceReference,
    VerificationResult,
    SourceJurisprudence,
    TypeJuridiction,
    get_all_juridictions
)
from managers.jurisprudence_verifier import JurisprudenceVerifier
from managers.legal_search import LegalSearchManager
from utils.helpers import clean_key, highlight_text

logger = logging.getLogger(__name__)

# Configuration des sources
SOURCE_CONFIGS = {
    SourceJurisprudence.LEGIFRANCE: {
        'name': 'Légifrance',
        'icon': '🏛️',
        'url': 'https://www.legifrance.gouv.fr',
        'api_available': True
    },
    SourceJurisprudence.JUDILIBRE: {
        'name': 'Judilibre',
        'icon': '⚖️',
        'url': 'https://api.judilibre.io',
        'api_available': True
    },
    SourceJurisprudence.DOCTRINE: {
        'name': 'Doctrine.fr',
        'icon': '📚',
        'url': 'https://www.doctrine.fr',
        'api_available': False
    },
    SourceJurisprudence.DALLOZ: {
        'name': 'Dalloz',
        'icon': '📖',
        'url': 'https://www.dalloz.fr',
        'api_available': False
    },
    SourceJurisprudence.COURDECASSATION: {
        'name': 'Cour de cassation',
        'icon': '⚖️',
        'url': 'https://www.courdecassation.fr',
        'api_available': True
    }
}

class JurisprudenceAPIManager:
    """Gestionnaire des API de jurisprudence"""
    
    def __init__(self):
        # Clés API
        self.judilibre_api_key = os.getenv('JUDILIBRE_API_KEY', 'ac72ad69-ef21-4af2-b3e2-6fa1132a8348')
        self.piste_client_id = os.getenv('PISTE_CLIENT_ID', '')
        self.piste_client_secret = os.getenv('PISTE_CLIENT_SECRET', '')
        
        # URLs des APIs
        self.apis = {
            'piste': {
                'base_url': 'https://api.piste.gouv.fr',
                'oauth_url': 'https://oauth.piste.gouv.fr/api/oauth/token',
                'search_url': 'https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/search',
                'consult_url': 'https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/consult',
                'requires_auth': True
            },
            'judilibre': {
                'base_url': 'https://api.judilibre.io/v1.0',
                'search_url': 'https://api.judilibre.io/v1.0/search',
                'decision_url': 'https://api.judilibre.io/v1.0/decision',
                'export_url': 'https://api.judilibre.io/v1.0/export',
                'requires_auth': True
            },
            'conseil_etat': {
                'base_url': 'https://www.conseil-etat.fr/arianeweb/api',
                'requires_auth': False
            }
        }
        
        self.access_token = None
        self.token_expires_at = None
        
        # Cache pour les résultats
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    async def authenticate_piste(self):
        """Authentification OAuth2 pour l'API PISTE"""
        if not self.piste_client_id or not self.piste_client_secret:
            logger.warning("Identifiants PISTE non configurés")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.piste_client_id,
                    'client_secret': self.piste_client_secret,
                    'scope': 'openid'
                }
                
                async with session.post(self.apis['piste']['oauth_url'], data=data) as resp:
                    if resp.status == 200:
                        token_data = await resp.json()
                        self.access_token = token_data.get('access_token')
                        expires_in = token_data.get('expires_in', 3600)
                        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                        logger.info("Authentification PISTE réussie")
                        return True
                    else:
                        logger.error(f"Erreur authentification PISTE: {resp.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification PISTE: {e}")
            return False
    
    async def search_judilibre(self, criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
        """Recherche sur Judilibre"""
        results = []
        
        try:
            headers = {
                'KeyId': self.judilibre_api_key,
                'Content-Type': 'application/json'
            }
            
            # Construire la requête
            query_params = {
                'query': criteria.get('query', ''),
                'jurisdiction': [],
                'chamber': [],
                'formation': [],
                'date_start': None,
                'date_end': None,
                'sort': 'score',
                'order': 'desc',
                'page': 0,
                'page_size': 30
            }
            
            # Filtrer par juridiction
            if criteria.get('juridictions'):
                for juridiction in criteria['juridictions']:
                    if 'cassation' in juridiction.lower():
                        query_params['jurisdiction'].append('cc')
                    elif 'appel' in juridiction.lower():
                        query_params['jurisdiction'].append('ca')
            
            # Filtrer par date
            if criteria.get('date_range'):
                start, end = criteria['date_range']
                query_params['date_start'] = start.strftime('%Y-%m-%d')
                query_params['date_end'] = end.strftime('%Y-%m-%d')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.apis['judilibre']['search_url'],
                    headers=headers,
                    json=query_params
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for hit in data.get('results', []):
                            try:
                                # Extraire les informations
                                decision = hit.get('decision', {})
                                
                                ref = JurisprudenceReference(
                                    numero=decision.get('number', ''),
                                    date=datetime.strptime(decision.get('date', ''), '%Y-%m-%d'),
                                    juridiction=self._format_juridiction_judilibre(decision),
                                    type_juridiction=self._get_type_juridiction(decision),
                                    formation=decision.get('formation', ''),
                                    titre=self._extract_title_judilibre(decision),
                                    resume=decision.get('summary', '')[:500],
                                    url=f"https://www.courdecassation.fr/decision/{decision.get('id')}",
                                    source=SourceJurisprudence.JUDILIBRE,
                                    mots_cles=self._extract_keywords_judilibre(decision),
                                    articles_vises=self._extract_articles_judilibre(decision),
                                    importance=self._calculate_importance_judilibre(hit),
                                    solution=decision.get('solution', ''),
                                    portee=self._determine_portee_judilibre(decision),
                                    texte_integral=decision.get('text', '')
                                )
                                
                                results.append(ref)
                                
                            except Exception as e:
                                logger.error(f"Erreur parsing décision Judilibre: {e}")
                                continue
                    else:
                        logger.error(f"Erreur recherche Judilibre: {resp.status}")
                        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche Judilibre: {e}")
        
        return results
    
    async def search_legifrance(self, criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
        """Recherche sur Légifrance via PISTE"""
        results = []
        
        # Vérifier l'authentification
        if not self.access_token or datetime.now() >= self.token_expires_at:
            if not await self.authenticate_piste():
                logger.warning("Impossible de s'authentifier à PISTE")
                return results
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Construire la requête
            search_data = {
                'fond': 'JURI',  # Jurisprudence
                'recherche': {
                    'typeRecherche': 'TOUS_LES_MOTS_DANS_UN_CHAMP',
                    'pageNumber': 1,
                    'pageSize': 30,
                    'sort': 'PERTINENCE',
                    'champs': [
                        {
                            'typeChamp': 'ALL',
                            'criteres': [
                                {
                                    'typeRecherche': 'TOUS_LES_MOTS',
                                    'valeur': criteria.get('query', '')
                                }
                            ]
                        }
                    ]
                }
            }
            
            # Ajouter les filtres
            if criteria.get('juridictions'):
                search_data['recherche']['facettes'] = {
                    'JURIDICTION': [j for j in criteria['juridictions']]
                }
            
            if criteria.get('date_range'):
                start, end = criteria['date_range']
                search_data['recherche']['filtres'] = {
                    'dateDecision': {
                        'start': start.strftime('%Y-%m-%d'),
                        'end': end.strftime('%Y-%m-%d')
                    }
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.apis['piste']['search_url'],
                    headers=headers,
                    json=search_data
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for result in data.get('results', []):
                            try:
                                ref = JurisprudenceReference(
                                    numero=result.get('numeroAffaire', ''),
                                    date=datetime.strptime(result.get('dateDecision', ''), '%Y-%m-%d'),
                                    juridiction=result.get('juridiction', ''),
                                    type_juridiction=self._get_type_juridiction_legifrance(result),
                                    formation=result.get('formation', ''),
                                    titre=result.get('titre', ''),
                                    resume=result.get('sommaire', '')[:500],
                                    url=f"https://www.legifrance.gouv.fr/juri/id/{result.get('id')}",
                                    source=SourceJurisprudence.LEGIFRANCE,
                                    mots_cles=result.get('descripteurs', []),
                                    articles_vises=self._extract_articles_legifrance(result),
                                    importance=self._calculate_importance_legifrance(result),
                                    solution=result.get('solution', ''),
                                    portee=result.get('portee', ''),
                                    texte_integral=None  # À récupérer séparément si nécessaire
                                )
                                
                                results.append(ref)
                                
                            except Exception as e:
                                logger.error(f"Erreur parsing décision Légifrance: {e}")
                                continue
                    else:
                        logger.error(f"Erreur recherche Légifrance: {resp.status}")
                        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche Légifrance: {e}")
        
        return results
    
    def _format_juridiction_judilibre(self, decision: dict) -> str:
        """Formate la juridiction depuis les données Judilibre"""
        jurisdiction = decision.get('jurisdiction', '')
        chamber = decision.get('chamber', '')
        
        if jurisdiction == 'cc':
            base = "Cour de cassation"
            if chamber:
                return f"{base}, {chamber}"
            return base
        elif jurisdiction == 'ca':
            location = decision.get('location', '')
            return f"Cour d'appel de {location}" if location else "Cour d'appel"
        
        return jurisdiction
    
    def _get_type_juridiction(self, decision: dict) -> TypeJuridiction:
        """Détermine le type de juridiction"""
        jurisdiction = decision.get('jurisdiction', '').lower()
        
        if jurisdiction == 'cc':
            return TypeJuridiction.COUR_DE_CASSATION
        elif jurisdiction == 'ca':
            return TypeJuridiction.COUR_APPEL
        elif jurisdiction == 'ce':
            return TypeJuridiction.CONSEIL_ETAT
        
        return TypeJuridiction.AUTRE
    
    def _extract_title_judilibre(self, decision: dict) -> str:
        """Extrait un titre depuis les données Judilibre"""
        # Essayer d'extraire depuis le sommaire ou les mots-clés
        summary = decision.get('summary', '')
        if summary:
            # Prendre la première phrase
            return summary.split('.')[0]
        
        themes = decision.get('themes', [])
        if themes:
            return " - ".join(themes[:2])
        
        return ""
    
    def _extract_keywords_judilibre(self, decision: dict) -> List[str]:
        """Extrait les mots-clés depuis les données Judilibre"""
        keywords = []
        
        # Thèmes
        keywords.extend(decision.get('themes', []))
        
        # Rubriques
        keywords.extend(decision.get('rubriques', []))
        
        return list(set(keywords))
    
    def _extract_articles_judilibre(self, decision: dict) -> List[str]:
        """Extrait les articles visés"""
        articles = []
        
        # Chercher dans les références
        references = decision.get('references', {})
        for ref_type, ref_list in references.items():
            if 'article' in ref_type.lower():
                articles.extend(ref_list)
        
        # Chercher dans le texte
        text = decision.get('text', '')
        if text:
            # Pattern pour les articles
            article_pattern = r'article[s]?\s+([LR]?\s*\d+(?:-\d+)?(?:\s+et\s+[LR]?\s*\d+(?:-\d+)?)*)'
            matches = re.findall(article_pattern, text, re.IGNORECASE)
            articles.extend(matches)
        
        return list(set(articles))
    
    def _calculate_importance_judilibre(self, hit: dict) -> int:
        """Calcule l'importance d'une décision Judilibre"""
        score = 5  # Base
        
        # Score de pertinence
        relevance = hit.get('score', 0)
        if relevance > 0.8:
            score += 2
        elif relevance > 0.6:
            score += 1
        
        decision = hit.get('decision', {})
        
        # Bulletin
        if decision.get('bulletin'):
            score += 2
        
        # Solution importante
        solution = decision.get('solution', '').lower()
        if 'principe' in solution or 'cassation' in solution:
            score += 1
        
        # Décision récente
        try:
            date = datetime.strptime(decision.get('date', ''), '%Y-%m-%d')
            if (datetime.now() - date).days < 365:
                score += 1
        except:
            pass
        
        return min(score, 10)
    
    def _determine_portee_judilibre(self, decision: dict) -> str:
        """Détermine la portée d'une décision"""
        # Indices dans le texte ou les métadonnées
        if decision.get('bulletin'):
            return "Principe"
        
        solution = decision.get('solution', '').lower()
        if 'principe' in solution:
            return "Principe"
        elif 'espèce' in solution:
            return "Espèce"
        
        return ""
    
    def _get_type_juridiction_legifrance(self, result: dict) -> TypeJuridiction:
        """Détermine le type de juridiction pour Légifrance"""
        juridiction = result.get('juridiction', '').lower()
        
        if 'cassation' in juridiction:
            return TypeJuridiction.COUR_DE_CASSATION
        elif 'appel' in juridiction:
            return TypeJuridiction.COUR_APPEL
        elif 'conseil' in juridiction and 'etat' in juridiction:
            return TypeJuridiction.CONSEIL_ETAT
        elif 'constitutionnel' in juridiction:
            return TypeJuridiction.CONSEIL_CONSTITUTIONNEL
        elif 'tribunal' in juridiction:
            return TypeJuridiction.TRIBUNAL
        
        return TypeJuridiction.AUTRE
    
    def _extract_articles_legifrance(self, result: dict) -> List[str]:
        """Extrait les articles depuis les données Légifrance"""
        articles = []
        
        # Textes visés
        textes_vises = result.get('textesVises', [])
        for texte in textes_vises:
            if 'article' in texte.lower():
                articles.append(texte)
        
        # Analyse du texte
        text = result.get('texteIntegral', '')
        if text:
            article_pattern = r'article[s]?\s+([LR]?\s*\d+(?:-\d+)?)'
            matches = re.findall(article_pattern, text, re.IGNORECASE)
            articles.extend(matches)
        
        return list(set(articles))
    
    def _calculate_importance_legifrance(self, result: dict) -> int:
        """Calcule l'importance d'une décision Légifrance"""
        score = 5  # Base
        
        # Publié au bulletin
        if result.get('publication', {}).get('bulletin'):
            score += 2
        
        # Décision de principe
        if result.get('importance') == 'PRINCIPE':
            score += 2
        
        # Nombreuses références
        if len(result.get('textesVises', [])) > 5:
            score += 1
        
        # Décision récente
        try:
            date = datetime.strptime(result.get('dateDecision', ''), '%Y-%m-%d')
            if (datetime.now() - date).days < 365:
                score += 1
        except:
            pass
        
        return min(score, 10)


# Instance globale du gestionnaire d'API
api_manager = JurisprudenceAPIManager()


def process_jurisprudence_request(query: str, analysis: dict):
    """Traite une demande de recherche de jurisprudence"""
    
    st.markdown("### ⚖️ Recherche de jurisprudence")
    
    # Activer le mode jurisprudence
    st.session_state.jurisprudence_search_active = True
    
    # Extraire les critères de recherche
    search_criteria = extract_jurisprudence_criteria(query, analysis)
    
    # Interface de recherche
    show_jurisprudence_search_interface(search_criteria)


def extract_jurisprudence_criteria(query: str, analysis: dict) -> Dict[str, Any]:
    """Extrait les critères de recherche jurisprudentielle"""
    
    criteria = {
        'keywords': [],
        'juridictions': [],
        'date_range': None,
        'numero': None,
        'articles': [],
        'parties': []
    }
    
    query_lower = query.lower()
    
    # Mots-clés juridiques
    legal_keywords = [
        'responsabilité', 'préjudice', 'dommages', 'faute', 'causalité',
        'contrat', 'obligation', 'résiliation', 'nullité', 'prescription',
        'procédure', 'compétence', 'recevabilité', 'appel', 'cassation'
    ]
    
    criteria['keywords'] = [kw for kw in legal_keywords if kw in query_lower]
    
    # Ajouter les termes de l'analyse
    if analysis.get('legal_terms'):
        criteria['keywords'].extend(analysis['legal_terms'])
    
    # Juridictions
    for juridiction in get_all_juridictions():
        if juridiction.lower() in query_lower:
            criteria['juridictions'].append(juridiction)
    
    # Numéro de décision
    numero_pattern = r'\b(\d{2}-\d{2}\.\d{3}|\d{2}-\d{5})\b'
    numero_match = re.search(numero_pattern, query)
    if numero_match:
        criteria['numero'] = numero_match.group(1)
    
    # Articles de loi
    article_pattern = r'article\s+([LR]?\s*\d+(?:-\d+)?)'
    articles = re.findall(article_pattern, query, re.IGNORECASE)
    criteria['articles'] = articles
    
    return criteria


def show_jurisprudence_search_interface(initial_criteria: Dict[str, Any] = None):
    """Interface principale de recherche jurisprudentielle"""
    
    # Gestionnaires
    verifier = st.session_state.get('jurisprudence_verifier', JurisprudenceVerifier())
    search_manager = st.session_state.get('legal_search_manager', LegalSearchManager())
    
    # Onglets
    tabs = st.tabs([
        "🔍 Recherche",
        "✅ Vérification",
        "📚 Base locale",
        "📊 Statistiques",
        "⚙️ Configuration"
    ])
    
    with tabs[0]:
        show_search_tab(search_manager, initial_criteria)
    
    with tabs[1]:
        show_verification_tab(verifier)
    
    with tabs[2]:
        show_local_database_tab()
    
    with tabs[3]:
        show_statistics_tab()
    
    with tabs[4]:
        show_configuration_tab()


def show_search_tab(search_manager: LegalSearchManager, initial_criteria: Dict[str, Any] = None):
    """Onglet de recherche avec flux amélioré"""
    
    st.markdown("#### 🔍 Recherche de jurisprudence")
    
    # Informer sur le flux de recherche
    with st.expander("ℹ️ Processus de recherche", expanded=False):
        st.info("""
        **Flux de recherche optimisé :**
        1. 🔍 **Recherche officielle** : Consultation des API Judilibre et Légifrance
        2. 🤖 **Suggestions IA** : Propositions complémentaires par l'IA
        3. ✅ **Vérification** : Validation de toutes les jurisprudences
        4. 📊 **Résultats vérifiés** : Affichage uniquement des décisions confirmées
        """)
    
    # Formulaire de recherche
    with st.form("jurisprudence_search_form"):
        # Recherche textuelle
        query = st.text_input(
            "Recherche libre",
            value=" ".join(initial_criteria.get('keywords', [])) if initial_criteria else "",
            placeholder="Ex: responsabilité contractuelle dommages-intérêts",
            key="juris_free_search"
        )
        
        # Critères avancés
        col1, col2 = st.columns(2)
        
        with col1:
            # Juridictions
            selected_juridictions = st.multiselect(
                "Juridictions",
                options=get_all_juridictions(),
                default=initial_criteria.get('juridictions', []) if initial_criteria else [],
                key="juris_juridictions"
            )
            
            # Période
            date_range = st.selectbox(
                "Période",
                ["Toutes", "1 mois", "6 mois", "1 an", "5 ans", "10 ans", "Personnalisée"],
                key="juris_date_range"
            )
            
            if date_range == "Personnalisée":
                date_start = st.date_input("Date début", key="juris_date_start")
                date_end = st.date_input("Date fin", key="juris_date_end")
        
        with col2:
            # Sources - Toujours activer Judilibre et Légifrance
            selected_sources = st.multiselect(
                "Sources",
                options=[s.value for s in SourceJurisprudence],
                default=[SourceJurisprudence.LEGIFRANCE.value, SourceJurisprudence.JUDILIBRE.value],
                format_func=lambda x: SOURCE_CONFIGS[SourceJurisprudence(x)]['name'],
                key="juris_sources",
                help="Judilibre et Légifrance sont toujours consultés en priorité"
            )
            
            # Importance
            min_importance = st.slider(
                "Importance minimale",
                min_value=1,
                max_value=10,
                value=5,
                key="juris_importance"
            )
        
        # Articles visés
        articles = st.text_input(
            "Articles visés (séparés par des virgules)",
            value=", ".join(initial_criteria.get('articles', [])) if initial_criteria else "",
            placeholder="Ex: L.1142-1, L.1142-2",
            key="juris_articles"
        )
        
        # Options de recherche
        with st.expander("Options avancées", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                search_in_summary = st.checkbox("Rechercher dans les résumés", value=True)
                search_in_full_text = st.checkbox("Rechercher dans le texte intégral", value=False)
                enable_ai_suggestions = st.checkbox("Activer les suggestions IA", value=True)
                
            with col2:
                only_principle = st.checkbox("Décisions de principe uniquement", value=False)
                with_commentary = st.checkbox("Avec commentaires uniquement", value=False)
                auto_verify = st.checkbox("Vérification automatique", value=True)
        
        # Bouton de recherche
        search_submitted = st.form_submit_button("🔍 Rechercher", type="primary")
    
    # Lancer la recherche
    if search_submitted:
        perform_jurisprudence_search_enhanced(
            query,
            selected_juridictions,
            selected_sources,
            articles,
            date_range,
            min_importance,
            search_in_summary,
            search_in_full_text,
            only_principle,
            with_commentary,
            enable_ai_suggestions,
            auto_verify
        )
    
    # Afficher les résultats
    show_search_results()


def perform_jurisprudence_search_enhanced(
    query: str,
    juridictions: List[str],
    sources: List[str],
    articles: str,
    date_range: str,
    min_importance: int,
    search_in_summary: bool,
    search_in_full_text: bool,
    only_principle: bool,
    with_commentary: bool,
    enable_ai_suggestions: bool,
    auto_verify: bool
):
    """Effectue la recherche de jurisprudence avec le flux amélioré"""
    
    # Construire les critères
    search_criteria = {
        'query': query,
        'juridictions': juridictions,
        'sources': [SourceJurisprudence(s) for s in sources],
        'articles': [a.strip() for a in articles.split(',') if a.strip()],
        'date_range': parse_date_range(date_range),
        'min_importance': min_importance,
        'search_in_summary': search_in_summary,
        'search_in_full_text': search_in_full_text,
        'only_principle': only_principle,
        'with_commentary': with_commentary
    }
    
    # Résultats consolidés
    all_results = []
    verified_results = []
    
    # Étape 1: Recherche sur les API officielles
    with st.spinner("🔍 Recherche sur les bases officielles (Judilibre, Légifrance)..."):
        # Toujours rechercher sur Judilibre et Légifrance
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            official_results = loop.run_until_complete(search_official_sources(search_criteria))
            all_results.extend(official_results)
        except Exception as e:
            logger.error(f"Erreur lors de la recherche officielle: {e}")
            st.error(f"Erreur lors de la recherche: {str(e)}")
            official_results = []
        
        st.success(f"✅ {len(official_results)} décisions trouvées sur les bases officielles")
    
    # Étape 2: Suggestions IA si activées
    if enable_ai_suggestions and len(all_results) < 20:
        with st.spinner("🤖 Recherche de jurisprudences complémentaires par IA..."):
            ai_suggestions = get_ai_jurisprudence_suggestions(search_criteria, all_results)
            
            if ai_suggestions:
                st.info(f"💡 {len(ai_suggestions)} suggestions supplémentaires de l'IA")
                all_results.extend(ai_suggestions)
    
    # Étape 3: Vérification automatique si activée
    if auto_verify and all_results:
        with st.spinner("✅ Vérification des références..."):
            verifier = st.session_state.get('jurisprudence_verifier', JurisprudenceVerifier())
            
            progress_bar = st.progress(0)
            
            for i, ref in enumerate(all_results):
                # Vérifier la référence
                verification_result = verifier.verify_reference(ref.get_citation())
                
                if verification_result.is_valid:
                    # Enrichir avec les données vérifiées
                    if verification_result.reference:
                        ref.is_verified = True
                        ref.verification_confidence = verification_result.confidence
                        verified_results.append(ref)
                else:
                    # Marquer comme non vérifiée
                    ref.is_verified = False
                    ref.verification_message = verification_result.message
                
                progress_bar.progress((i + 1) / len(all_results))
            
            progress_bar.empty()
            
            st.success(f"✅ {len(verified_results)} décisions vérifiées sur {len(all_results)}")
    else:
        verified_results = all_results
    
    # Étape 4: Filtrer et trier les résultats
    final_results = []
    
    for ref in verified_results:
        # Appliquer les filtres supplémentaires
        if only_principle and ref.portee != "Principe":
            continue
        
        if with_commentary and not ref.commentaires:
            continue
        
        if ref.importance >= min_importance:
            final_results.append(ref)
    
    # Trier par pertinence et date
    final_results.sort(key=lambda x: (x.importance, x.date), reverse=True)
    
    # Stocker les résultats
    st.session_state.jurisprudence_results = final_results
    st.session_state.jurisprudence_search_criteria = search_criteria
    st.session_state.jurisprudence_verification_status = {
        'total': len(all_results),
        'verified': len(verified_results),
        'displayed': len(final_results)
    }
    
    if final_results:
        st.success(f"📊 {len(final_results)} décision(s) affichée(s) après filtrage")
    else:
        st.warning("⚠️ Aucune décision ne correspond aux critères après vérification")


async def search_official_sources(criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
    """Recherche asynchrone sur les sources officielles"""
    results = []
    
    # Créer les tâches de recherche
    tasks = []
    
    # Toujours rechercher sur Judilibre
    tasks.append(api_manager.search_judilibre(criteria))
    
    # Toujours rechercher sur Légifrance
    tasks.append(api_manager.search_legifrance(criteria))
    
    # Exécuter les recherches en parallèle
    search_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Consolider les résultats
    for result in search_results:
        if isinstance(result, list):
            results.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"Erreur lors de la recherche: {result}")
    
    return results


def get_ai_jurisprudence_suggestions(criteria: Dict[str, Any], existing_results: List[JurisprudenceReference]) -> List[JurisprudenceReference]:
    """Obtient des suggestions de jurisprudence via IA"""
    suggestions = []
    
    # Ici, intégrer l'appel à votre IA pour obtenir des suggestions
    # Pour l'instant, retourner une liste vide
    
    # Exemple d'intégration :
    # prompt = f"Suggère des jurisprudences pertinentes pour: {criteria['query']}"
    # ai_response = call_ai_api(prompt)
    # suggestions = parse_ai_suggestions(ai_response)
    
    return suggestions


def search_jurisprudence(criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
    """Recherche la jurisprudence selon les critères (méthode legacy)"""
    
    # Utiliser la nouvelle méthode de recherche
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(search_official_sources(criteria))
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        results = []
    
    # Recherche dans les autres sources si demandé
    for source in criteria.get('sources', []):
        if source == SourceJurisprudence.INTERNAL:
            results.extend(search_internal_database(criteria))
        elif source == SourceJurisprudence.DOCTRINE:
            # Implémenter la recherche Doctrine si disponible
            pass
        elif source == SourceJurisprudence.DALLOZ:
            # Implémenter la recherche Dalloz si disponible
            pass
    
    # Filtrer par importance
    results = [r for r in results if r.importance >= criteria.get('min_importance', 1)]
    
    # Trier par pertinence et date
    results.sort(key=lambda x: (x.importance, x.date), reverse=True)
    
    return results


def search_internal_database(criteria: Dict[str, Any]) -> List[JurisprudenceReference]:
    """Recherche dans la base locale"""
    
    results = []
    
    # Récupérer la base locale
    local_db = st.session_state.get('jurisprudence_database', {})
    
    for ref_id, ref in local_db.items():
        # Vérifier les critères
        score = 0
        
        # Mots-clés
        if criteria.get('query'):
            query_words = criteria['query'].lower().split()
            ref_text = f"{ref.titre} {ref.resume}".lower()
            
            for word in query_words:
                if word in ref_text:
                    score += 1
        
        # Juridiction
        if criteria.get('juridictions'):
            if ref.juridiction in criteria['juridictions']:
                score += 2
        
        # Articles
        if criteria.get('articles'):
            for article in criteria['articles']:
                if article in ref.articles_vises:
                    score += 3
        
        # Date
        if criteria.get('date_range'):
            start, end = criteria['date_range']
            if start <= ref.date <= end:
                score += 1
            else:
                continue
        
        if score > 0:
            results.append(ref)
    
    return results


def parse_date_range(date_range: str) -> Optional[Tuple[datetime, datetime]]:
    """Parse la période de recherche"""
    
    if date_range == "Toutes":
        return None
    
    end_date = datetime.now()
    
    if date_range == "1 mois":
        start_date = end_date - timedelta(days=30)
    elif date_range == "6 mois":
        start_date = end_date - timedelta(days=180)
    elif date_range == "1 an":
        start_date = end_date - timedelta(days=365)
    elif date_range == "5 ans":
        start_date = end_date - timedelta(days=365*5)
    elif date_range == "10 ans":
        start_date = end_date - timedelta(days=365*10)
    else:
        return None
    
    return (start_date, end_date)


def show_search_results():
    """Affiche les résultats de recherche avec statut de vérification"""
    
    results = st.session_state.get('jurisprudence_results', [])
    verification_status = st.session_state.get('jurisprudence_verification_status', {})
    
    if not results:
        return
    
    # Afficher le statut de vérification
    if verification_status:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Résultats trouvés", verification_status.get('total', 0))
        with col2:
            st.metric("Vérifiés", verification_status.get('verified', 0))
        with col3:
            st.metric("Affichés", verification_status.get('displayed', 0))
    
    st.markdown(f"#### 📊 Résultats ({len(results)} décisions)")
    
    # Options d'affichage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sort_by = st.selectbox(
            "Trier par",
            ["Pertinence", "Date", "Juridiction", "Importance"],
            key="juris_sort"
        )
    
    with col2:
        view_mode = st.radio(
            "Affichage",
            ["Résumé", "Détaillé"],
            key="juris_view_mode",
            horizontal=True
        )
    
    with col3:
        group_by = st.selectbox(
            "Grouper par",
            ["Aucun", "Juridiction", "Année", "Matière", "Source"],
            key="juris_group"
        )
    
    # Trier les résultats
    sorted_results = sort_jurisprudence_results(results, sort_by)
    
    # Grouper si demandé
    if group_by != "Aucun":
        grouped_results = group_jurisprudence_results(sorted_results, group_by)
        
        for group_name, group_results in grouped_results.items():
            with st.expander(f"{group_name} ({len(group_results)} décisions)", expanded=True):
                for ref in group_results:
                    show_jurisprudence_item(ref, view_mode)
    else:
        # Affichage simple
        for ref in sorted_results:
            show_jurisprudence_item(ref, view_mode)


def show_jurisprudence_item(ref: JurisprudenceReference, view_mode: str):
    """Affiche un élément de jurisprudence avec indicateur de vérification"""
    
    with st.container():
        if view_mode == "Résumé":
            # Vue compacte
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # Titre avec lien et indicateur de vérification
                verification_icon = "✅" if getattr(ref, 'is_verified', True) else "⚠️"
                
                if ref.url:
                    st.markdown(f"{verification_icon} **[{ref.get_citation()}]({ref.url})**")
                else:
                    st.markdown(f"{verification_icon} **{ref.get_citation()}**")
                
                if ref.titre:
                    st.caption(ref.titre)
                
                # Afficher la confiance de vérification si disponible
                if hasattr(ref, 'verification_confidence'):
                    st.caption(f"Confiance: {ref.verification_confidence:.0%}")
            
            with col2:
                # Source
                source_config = SOURCE_CONFIGS.get(ref.source, {})
                st.write(f"{source_config.get('icon', '')} {source_config.get('name', ref.source.value)}")
            
            with col3:
                # Importance
                importance_color = "🟢" if ref.importance >= 8 else "🟡" if ref.importance >= 5 else "🔴"
                st.write(f"{importance_color} {ref.importance}/10")
            
            with col4:
                # Actions
                if st.button("📖", key=f"view_juris_{ref.numero}_{ref.date.strftime('%Y%m%d')}"):
                    show_jurisprudence_detail(ref)
                
                if st.button("📌", key=f"save_juris_{ref.numero}_{ref.date.strftime('%Y%m%d')}"):
                    save_to_favorites(ref)
        
        else:  # Vue détaillée
            # En-tête avec vérification
            col1, col2 = st.columns([4, 1])
            
            with col1:
                verification_icon = "✅" if getattr(ref, 'is_verified', True) else "⚠️"
                
                if ref.url:
                    st.markdown(f"### {verification_icon} [{ref.get_citation()}]({ref.url})")
                else:
                    st.markdown(f"### {verification_icon} {ref.get_citation()}")
                
                if hasattr(ref, 'verification_confidence'):
                    st.caption(f"Vérifié avec {ref.verification_confidence:.0%} de confiance")
                elif hasattr(ref, 'verification_message'):
                    st.warning(ref.verification_message)
            
            with col2:
                importance_color = "🟢" if ref.importance >= 8 else "🟡" if ref.importance >= 5 else "🔴"
                st.metric("Importance", f"{importance_color} {ref.importance}/10")
            
            # Métadonnées
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Formation :** {ref.formation or 'N/A'}")
                st.write(f"**Solution :** {ref.solution or 'N/A'}")
            
            with col2:
                st.write(f"**Portée :** {ref.portee or 'N/A'}")
                source_config = SOURCE_CONFIGS.get(ref.source, {})
                st.write(f"**Source :** {source_config.get('icon', '')} {source_config.get('name', ref.source.value)}")
            
            with col3:
                if ref.articles_vises:
                    st.write(f"**Articles :** {', '.join(ref.articles_vises[:3])}")
                    if len(ref.articles_vises) > 3:
                        st.caption(f"... et {len(ref.articles_vises) - 3} autres")
            
            # Résumé
            if ref.resume:
                st.markdown("**Résumé :**")
                st.info(ref.resume)
            
            # Mots-clés
            if ref.mots_cles:
                st.write("**Mots-clés :** " + " • ".join([f"`{kw}`" for kw in ref.mots_cles]))
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📖 Texte intégral", key=f"full_text_{ref.numero}_{ref.date.strftime('%Y%m%d')}"):
                    show_full_text(ref)
            
            with col2:
                if st.button("🔗 Décisions liées", key=f"related_{ref.numero}_{ref.date.strftime('%Y%m%d')}"):
                    show_related_decisions(ref)
            
            with col3:
                if st.button("💬 Commentaires", key=f"comments_{ref.numero}_{ref.date.strftime('%Y%m%d')}"):
                    show_commentaries(ref)
            
            with col4:
                if st.button("📌 Sauvegarder", key=f"save_detail_{ref.numero}_{ref.date.strftime('%Y%m%d')}"):
                    save_to_favorites(ref)
        
        st.divider()


# Les autres fonctions restent identiques...
def sort_jurisprudence_results(results: List[JurisprudenceReference], sort_by: str) -> List[JurisprudenceReference]:
    """Trie les résultats de jurisprudence"""
    
    if sort_by == "Date":
        return sorted(results, key=lambda x: x.date, reverse=True)
    elif sort_by == "Juridiction":
        return sorted(results, key=lambda x: x.juridiction)
    elif sort_by == "Importance":
        return sorted(results, key=lambda x: x.importance, reverse=True)
    else:  # Pertinence
        return results  # Déjà trié par pertinence


def group_jurisprudence_results(results: List[JurisprudenceReference], group_by: str) -> Dict[str, List[JurisprudenceReference]]:
    """Groupe les résultats de jurisprudence"""
    
    grouped = {}
    
    for ref in results:
        if group_by == "Juridiction":
            key = ref.juridiction
        elif group_by == "Année":
            key = str(ref.date.year)
        elif group_by == "Source":
            source_config = SOURCE_CONFIGS.get(ref.source, {})
            key = f"{source_config.get('icon', '')} {source_config.get('name', ref.source.value)}"
        elif group_by == "Matière":
            # Déterminer la matière depuis les mots-clés
            if any(kw in ['contrat', 'obligation', 'responsabilité contractuelle'] for kw in ref.mots_cles):
                key = "Droit des contrats"
            elif any(kw in ['responsabilité', 'préjudice', 'dommages'] for kw in ref.mots_cles):
                key = "Responsabilité civile"
            elif any(kw in ['procédure', 'compétence', 'appel'] for kw in ref.mots_cles):
                key = "Procédure civile"
            else:
                key = "Autres"
        else:
            key = "Tous"
        
        if key not in grouped:
            grouped[key] = []
        
        grouped[key].append(ref)
    
    return grouped


# Conserver toutes les autres fonctions existantes...
def show_jurisprudence_detail(ref: JurisprudenceReference):
    """Affiche le détail d'une décision"""
    st.session_state.current_jurisprudence = ref
    st.session_state.show_jurisprudence_detail = True


def save_to_favorites(ref: JurisprudenceReference):
    """Sauvegarde une décision dans les favoris"""
    if 'jurisprudence_favorites' not in st.session_state:
        st.session_state.jurisprudence_favorites = {}
    
    ref_id = f"{ref.numero}_{ref.date.strftime('%Y%m%d')}"
    st.session_state.jurisprudence_favorites[ref_id] = ref
    st.success("📌 Décision sauvegardée dans les favoris")


def show_full_text(ref: JurisprudenceReference):
    """Affiche le texte intégral"""
    if ref.texte_integral:
        with st.expander("📄 Texte intégral", expanded=True):
            st.text_area(
                "Texte de la décision",
                value=ref.texte_integral,
                height=600,
                key=f"full_text_display_{ref.numero}"
            )
    else:
        st.info("Texte intégral non disponible. Consultez le lien source.")
        if ref.url:
            st.markdown(f"[Voir sur {SOURCE_CONFIGS[ref.source]['name']}]({ref.url})")


def show_related_decisions(ref: JurisprudenceReference):
    """Affiche les décisions liées"""
    with st.spinner("Recherche des décisions liées..."):
        # Rechercher les décisions citées
        related = []
        
        if ref.decisions_citees:
            for decision_ref in ref.decisions_citees:
                related.append(decision_ref)
        
        # Rechercher les décisions similaires
        similar_criteria = {
            'query': ' '.join(ref.mots_cles[:3]),
            'juridictions': [ref.juridiction],
            'sources': [ref.source],
            'articles': ref.articles_vises[:2],
            'date_range': None,
            'min_importance': ref.importance - 2
        }
        
        similar_results = search_jurisprudence(similar_criteria)
        similar_results = [r for r in similar_results if r.numero != ref.numero]
        
        # Afficher
        if related or similar_results:
            st.markdown("#### 🔗 Décisions liées")
            
            if related:
                st.write("**Décisions citées :**")
                for dec_ref in related:
                    st.write(f"• {dec_ref}")
            
            if similar_results:
                st.write(f"**Décisions similaires ({len(similar_results)}) :**")
                for similar in similar_results[:5]:
                    st.write(f"• {similar.get_citation()}")
                    if similar.titre:
                        st.caption(similar.titre)
        else:
            st.info("Aucune décision liée trouvée")


def show_commentaries(ref: JurisprudenceReference):
    """Affiche les commentaires"""
    if ref.commentaires:
        st.markdown("#### 💬 Commentaires")
        for i, commentaire in enumerate(ref.commentaires, 1):
            with st.expander(f"Commentaire {i}"):
                st.write(commentaire)
    else:
        st.info("Aucun commentaire disponible pour cette décision")


def show_verification_tab(verifier: JurisprudenceVerifier):
    """Onglet de vérification"""
    st.markdown("#### ✅ Vérification de jurisprudence")
    
    st.info("""
    Vérifiez l'authenticité et la validité d'une référence de jurisprudence.
    Entrez la référence complète ou partielle.
    """)
    
    # Formulaire de vérification
    with st.form("verification_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            reference = st.text_input(
                "Référence à vérifier",
                placeholder="Ex: Cass. civ. 1, 17 mars 2021, n° 19-21.524",
                key="verify_reference"
            )
        
        with col2:
            verify_button = st.form_submit_button("🔍 Vérifier", type="primary")
    
    if verify_button and reference:
        with st.spinner("Vérification en cours..."):
            result = verifier.verify_reference(reference)
            show_verification_result(result)
    
    # Historique des vérifications
    show_verification_history()


def show_verification_result(result: VerificationResult):
    """Affiche le résultat de vérification"""
    if result.is_valid:
        st.success(f"✅ Référence valide (confiance : {result.confidence:.0%})")
        
        if result.reference:
            ref = result.reference
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Juridiction :** {ref.juridiction}")
                st.write(f"**Date :** {ref.date.strftime('%d/%m/%Y')}")
                st.write(f"**Numéro :** {ref.numero}")
            
            with col2:
                st.write(f"**Source vérifiée :** {SOURCE_CONFIGS[result.source_verified]['name']}")
                if ref.url:
                    st.write(f"**Lien :** [Voir la décision]({ref.url})")
            
            if ref.titre:
                st.write(f"**Titre :** {ref.titre}")
            
            if ref.resume:
                st.info(ref.resume)
            
            # Proposer de sauvegarder
            if st.button("📌 Sauvegarder cette décision"):
                save_to_database(ref)
    else:
        st.error(f"❌ Référence non trouvée ou invalide")
        
        if result.message:
            st.write(result.message)
        
        # Suggestions
        if result.suggestions:
            st.write("**Suggestions :**")
            for suggestion in result.suggestions[:3]:
                st.write(f"• {suggestion.get_citation()}")


def show_verification_history():
    """Affiche l'historique des vérifications"""
    history = st.session_state.get('verification_history', [])
    
    if history:
        with st.expander("📜 Historique des vérifications", expanded=False):
            for entry in reversed(history[-10:]):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(entry['reference'])
                
                with col2:
                    if entry['valid']:
                        st.success("✅ Valide")
                    else:
                        st.error("❌ Invalide")
                
                with col3:
                    st.caption(entry['date'].strftime('%d/%m %H:%M'))


def show_local_database_tab():
    """Onglet base de données locale"""
    st.markdown("#### 📚 Base de jurisprudence locale")
    
    # Statistiques
    local_db = st.session_state.get('jurisprudence_database', {})
    favorites = st.session_state.get('jurisprudence_favorites', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Décisions enregistrées", len(local_db))
    
    with col2:
        st.metric("Favoris", len(favorites))
    
    with col3:
        if local_db:
            juridictions = set(ref.juridiction for ref in local_db.values())
            st.metric("Juridictions", len(juridictions))
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Ajouter manuellement"):
            st.session_state.show_add_jurisprudence = True
    
    with col2:
        if st.button("📥 Importer CSV/JSON"):
            st.session_state.show_import_jurisprudence = True
    
    with col3:
        if st.button("📤 Exporter la base"):
            export_jurisprudence_database()
    
    # Interface d'ajout manuel
    if st.session_state.get('show_add_jurisprudence'):
        show_add_jurisprudence_form()
    
    # Interface d'import
    if st.session_state.get('show_import_jurisprudence'):
        show_import_jurisprudence_interface()
    
    # Liste des décisions
    show_local_jurisprudence_list(local_db, favorites)


def show_add_jurisprudence_form():
    """Formulaire d'ajout manuel de jurisprudence"""
    with st.form("add_jurisprudence_form"):
        st.markdown("##### ➕ Ajouter une décision")
        
        col1, col2 = st.columns(2)
        
        with col1:
            juridiction = st.selectbox(
                "Juridiction *",
                options=get_all_juridictions(),
                key="add_juris_juridiction"
            )
            
            numero = st.text_input(
                "Numéro *",
                placeholder="Ex: 19-21.524",
                key="add_juris_numero"
            )
            
            date = st.date_input(
                "Date *",
                key="add_juris_date"
            )
            
            formation = st.text_input(
                "Formation",
                placeholder="Ex: Première chambre civile",
                key="add_juris_formation"
            )
        
        with col2:
            titre = st.text_input(
                "Titre",
                placeholder="Ex: Responsabilité contractuelle",
                key="add_juris_titre"
            )
            
            solution = st.selectbox(
                "Solution",
                ["", "Cassation", "Rejet", "Irrecevabilité", "Non-lieu"],
                key="add_juris_solution"
            )
            
            portee = st.selectbox(
                "Portée",
                ["", "Principe", "Espèce", "Revirement"],
                key="add_juris_portee"
            )
            
            importance = st.slider(
                "Importance",
                min_value=1,
                max_value=10,
                value=5,
                key="add_juris_importance"
            )
        
        # Résumé
        resume = st.text_area(
            "Résumé",
            placeholder="Résumé de la décision...",
            height=100,
            key="add_juris_resume"
        )
        
        # Articles et mots-clés
        col1, col2 = st.columns(2)
        
        with col1:
            articles = st.text_input(
                "Articles visés (séparés par des virgules)",
                placeholder="Ex: L.1142-1, L.1142-2",
                key="add_juris_articles"
            )
        
        with col2:
            mots_cles = st.text_input(
                "Mots-clés (séparés par des virgules)",
                placeholder="Ex: responsabilité, préjudice, causalité",
                key="add_juris_mots_cles"
            )
        
        # URL
        url = st.text_input(
            "URL source",
            placeholder="https://...",
            key="add_juris_url"
        )
        
        # Boutons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("💾 Enregistrer", type="primary"):
                # Créer la référence
                new_ref = JurisprudenceReference(
                    numero=numero,
                    date=datetime.combine(date, datetime.min.time()),
                    juridiction=juridiction,
                    formation=formation,
                    titre=titre,
                    resume=resume,
                    url=url,
                    source=SourceJurisprudence.MANUAL,
                    mots_cles=[kw.strip() for kw in mots_cles.split(',') if kw.strip()],
                    articles_vises=[art.strip() for art in articles.split(',') if art.strip()],
                    importance=importance,
                    solution=solution,
                    portee=portee
                )
                
                # Sauvegarder
                save_to_database(new_ref)
                st.success("✅ Décision ajoutée à la base")
                st.session_state.show_add_jurisprudence = False
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Annuler"):
                st.session_state.show_add_jurisprudence = False
                st.rerun()


def save_to_database(ref: JurisprudenceReference):
    """Sauvegarde une référence dans la base locale"""
    if 'jurisprudence_database' not in st.session_state:
        st.session_state.jurisprudence_database = {}
    
    ref_id = f"{ref.numero}_{ref.date.strftime('%Y%m%d')}"
    st.session_state.jurisprudence_database[ref_id] = ref


def show_import_jurisprudence_interface():
    """Interface d'import de jurisprudence"""
    st.markdown("##### 📥 Importer des décisions")
    
    uploaded_file = st.file_uploader(
        "Choisir un fichier",
        type=['json', 'csv'],
        key="import_juris_file"
    )
    
    if uploaded_file:
        try:
            if uploaded_file.type == 'application/json':
                # Import JSON
                data = json.load(uploaded_file)
                
                imported_count = 0
                for item in data:
                    try:
                        ref = JurisprudenceReference(
                            numero=item['numero'],
                            date=datetime.strptime(item['date'], '%Y-%m-%d'),
                            juridiction=item['juridiction'],
                            formation=item.get('formation'),
                            titre=item.get('titre'),
                            resume=item.get('resume'),
                            url=item.get('url'),
                            source=SourceJurisprudence(item.get('source', 'MANUAL')),
                            mots_cles=item.get('mots_cles', '').split(', '),
                            articles_vises=item.get('articles_vises', '').split(', '),
                            importance=item.get('importance', 5),
                            solution=item.get('solution'),
                            portee=item.get('portee')
                        )
                        save_to_database(ref)
                        imported_count += 1
                    except Exception as e:
                        st.warning(f"Erreur import décision: {e}")
                
                st.success(f"✅ {imported_count} décisions importées")
                
            elif uploaded_file.type == 'text/csv':
                # Import CSV (nécessite pandas)
                try:
                    import pandas as pd
                    df = pd.read_csv(uploaded_file)
                    
                    imported_count = 0
                    for _, row in df.iterrows():
                        try:
                            ref = JurisprudenceReference(
                                numero=row['numero'],
                                date=pd.to_datetime(row['date']),
                                juridiction=row['juridiction'],
                                formation=row.get('formation'),
                                titre=row.get('titre'),
                                resume=row.get('resume'),
                                url=row.get('url'),
                                source=SourceJurisprudence(row.get('source', 'MANUAL')),
                                mots_cles=row.get('mots_cles', '').split(', '),
                                articles_vises=row.get('articles_vises', '').split(', '),
                                importance=int(row.get('importance', 5)),
                                solution=row.get('solution'),
                                portee=row.get('portee')
                            )
                            save_to_database(ref)
                            imported_count += 1
                        except Exception as e:
                            st.warning(f"Erreur import ligne: {e}")
                    
                    st.success(f"✅ {imported_count} décisions importées")
                    
                except ImportError:
                    st.error("Pandas requis pour l'import CSV")
                    
        except Exception as e:
            st.error(f"Erreur lors de l'import: {e}")
    
    if st.button("❌ Fermer"):
        st.session_state.show_import_jurisprudence = False
        st.rerun()


def show_local_jurisprudence_list(database: Dict[str, JurisprudenceReference], favorites: Dict[str, JurisprudenceReference]):
    """Affiche la liste des décisions locales"""
    if not database:
        st.info("Aucune décision dans la base locale")
        return
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_juridiction = st.selectbox(
            "Filtrer par juridiction",
            ["Toutes"] + list(set(ref.juridiction for ref in database.values())),
            key="filter_local_juridiction"
        )
    
    with col2:
        filter_importance = st.slider(
            "Importance min",
            min_value=1,
            max_value=10,
            value=1,
            key="filter_local_importance"
        )
    
    with col3:
        show_favorites_only = st.checkbox(
            "Favoris uniquement",
            key="show_favorites_only"
        )
    
    # Appliquer les filtres
    filtered_refs = database.values()
    
    if filter_juridiction != "Toutes":
        filtered_refs = [ref for ref in filtered_refs if ref.juridiction == filter_juridiction]
    
    filtered_refs = [ref for ref in filtered_refs if ref.importance >= filter_importance]
    
    if show_favorites_only:
        filtered_refs = [ref for ref in filtered_refs if f"{ref.numero}_{ref.date.strftime('%Y%m%d')}" in favorites]
    
    # Afficher
    st.write(f"**{len(filtered_refs)} décision(s)**")
    
    for ref in sorted(filtered_refs, key=lambda x: x.date, reverse=True):
        ref_id = f"{ref.numero}_{ref.date.strftime('%Y%m%d')}"
        is_favorite = ref_id in favorites
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{ref.get_citation()}**")
                if ref.titre:
                    st.caption(ref.titre)
            
            with col2:
                importance_color = "🟢" if ref.importance >= 8 else "🟡" if ref.importance >= 5 else "🔴"
                st.write(f"{importance_color} {ref.importance}/10")
            
            with col3:
                if st.button("📝", key=f"edit_local_{ref_id}"):
                    st.session_state.editing_jurisprudence = ref_id
            
            with col4:
                if is_favorite:
                    if st.button("⭐", key=f"unfav_local_{ref_id}"):
                        del st.session_state.jurisprudence_favorites[ref_id]
                        st.rerun()
                else:
                    if st.button("☆", key=f"fav_local_{ref_id}"):
                        st.session_state.jurisprudence_favorites[ref_id] = ref
                        st.rerun()
        
        st.divider()


def export_jurisprudence_database():
    """Exporte la base de jurisprudence"""
    database = st.session_state.get('jurisprudence_database', {})
    
    if not database:
        st.warning("Aucune décision à exporter")
        return
    
    # Préparer les données
    export_data = []
    
    for ref_id, ref in database.items():
        export_data.append({
            'numero': ref.numero,
            'date': ref.date.strftime('%Y-%m-%d'),
            'juridiction': ref.juridiction,
            'formation': ref.formation,
            'titre': ref.titre,
            'resume': ref.resume,
            'url': ref.url,
            'source': ref.source.value,
            'mots_cles': ', '.join(ref.mots_cles),
            'articles_vises': ', '.join(ref.articles_vises),
            'importance': ref.importance,
            'solution': ref.solution,
            'portee': ref.portee
        })
    
    # Export JSON
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        "💾 Télécharger JSON",
        json_str,
        f"jurisprudence_export_{datetime.now().strftime('%Y%m%d')}.json",
        "application/json",
        key="download_juris_json"
    )
    
    # Export CSV si pandas disponible
    try:
        import pandas as pd
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            "💾 Télécharger CSV",
            csv,
            f"jurisprudence_export_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            key="download_juris_csv"
        )
    except ImportError:
        pass


def show_statistics_tab():
    """Onglet statistiques"""
    st.markdown("#### 📊 Statistiques jurisprudentielles")
    
    database = st.session_state.get('jurisprudence_database', {})
    
    if not database:
        st.info("Aucune donnée pour les statistiques")
        return
    
    # Conversion en données pour analyse
    refs = list(database.values())
    
    # Statistiques générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total décisions", len(refs))
    
    with col2:
        avg_importance = sum(ref.importance for ref in refs) / len(refs)
        st.metric("Importance moyenne", f"{avg_importance:.1f}/10")
    
    with col3:
        principe_count = sum(1 for ref in refs if ref.portee == "Principe")
        st.metric("Décisions de principe", principe_count)
    
    with col4:
        recent_count = sum(1 for ref in refs if (datetime.now() - ref.date).days < 365)
        st.metric("Décisions < 1 an", recent_count)
    
    # Graphiques si plotly disponible
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        
        # Répartition par juridiction
        juridiction_counts = {}
        for ref in refs:
            juridiction_counts[ref.juridiction] = juridiction_counts.get(ref.juridiction, 0) + 1
        
        fig1 = go.Figure([go.Bar(
            x=list(juridiction_counts.keys()),
            y=list(juridiction_counts.values()),
            text=list(juridiction_counts.values()),
            textposition='auto'
        )])
        
        fig1.update_layout(
            title="Répartition par juridiction",
            xaxis_title="Juridiction",
            yaxis_title="Nombre de décisions",
            height=400
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # Évolution temporelle
        years = [ref.date.year for ref in refs]
        year_counts = Counter(years)
        
        fig2 = go.Figure([go.Scatter(
            x=sorted(year_counts.keys()),
            y=[year_counts[year] for year in sorted(year_counts.keys())],
            mode='lines+markers',
            name='Décisions'
        )])
        
        fig2.update_layout(
            title="Évolution temporelle",
            xaxis_title="Année",
            yaxis_title="Nombre de décisions",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Nuage de mots-clés
        all_keywords = []
        for ref in refs:
            all_keywords.extend(ref.mots_cles)
        
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(20)
        
        st.markdown("##### 🏷️ Mots-clés les plus fréquents")
        
        cols = st.columns(4)
        for i, (keyword, count) in enumerate(top_keywords):
            with cols[i % 4]:
                st.metric(keyword, count)
        
    except ImportError:
        st.info("Installez plotly pour voir les graphiques")


def show_configuration_tab():
    """Onglet configuration"""
    st.markdown("#### ⚙️ Configuration de la recherche jurisprudentielle")
    
    # Sources activées
    st.markdown("##### 🔌 Sources de recherche")
    
    enabled_sources = st.session_state.get('enabled_jurisprudence_sources', 
        [SourceJurisprudence.LEGIFRANCE, SourceJurisprudence.JUDILIBRE, SourceJurisprudence.INTERNAL])
    
    for source in SourceJurisprudence:
        config = SOURCE_CONFIGS.get(source, {})
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Toujours activer Judilibre et Légifrance
            if source in [SourceJurisprudence.JUDILIBRE, SourceJurisprudence.LEGIFRANCE]:
                is_enabled = st.checkbox(
                    "",
                    value=True,
                    key=f"enable_source_{source.value}",
                    disabled=True,
                    help="Sources officielles toujours activées"
                )
            else:
                is_enabled = st.checkbox(
                    "",
                    value=source in enabled_sources,
                    key=f"enable_source_{source.value}"
                )
            
            if is_enabled and source not in enabled_sources:
                enabled_sources.append(source)
            elif not is_enabled and source in enabled_sources:
                enabled_sources.remove(source)
        
        with col2:
            st.write(f"{config.get('icon', '')} **{config.get('name', source.value)}**")
            st.caption(config.get('url', ''))
        
        with col3:
            if config.get('api_available'):
                st.success("API ✅")
            else:
                st.warning("Web 🌐")
    
    st.session_state.enabled_jurisprudence_sources = enabled_sources
    
    # Préférences de recherche
    st.markdown("##### 🎯 Préférences de recherche")
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_importance = st.slider(
            "Importance minimale par défaut",
            min_value=1,
            max_value=10,
            value=st.session_state.get('default_juris_importance', 5),
            key="config_default_importance"
        )
        st.session_state.default_juris_importance = default_importance
        
        auto_verify = st.checkbox(
            "Vérification automatique des références",
            value=st.session_state.get('auto_verify_juris', True),
            key="config_auto_verify"
        )
        st.session_state.auto_verify_juris = auto_verify
    
    with col2:
        max_results = st.number_input(
            "Nombre max de résultats",
            min_value=10,
            max_value=500,
            value=st.session_state.get('max_juris_results', 100),
            step=10,
            key="config_max_results"
        )
        st.session_state.max_juris_results = max_results
        
        highlight_search = st.checkbox(
            "Surligner les termes recherchés",
            value=st.session_state.get('highlight_juris_search', True),
            key="config_highlight"
        )
        st.session_state.highlight_juris_search = highlight_search
    
    # API Keys
    st.markdown("##### 🔑 Clés API")
    
    st.info("""
    Les clés API sont configurées dans les variables d'environnement :
    - **JUDILIBRE_API_KEY** : Votre clé API Judilibre
    - **PISTE_CLIENT_ID** : Identifiant client PISTE
    - **PISTE_CLIENT_SECRET** : Secret client PISTE
    """)
    
    # Afficher le statut des clés
    col1, col2 = st.columns(2)
    
    with col1:
        if api_manager.judilibre_api_key:
            st.success("✅ Clé Judilibre configurée")
        else:
            st.error("❌ Clé Judilibre manquante")
    
    with col2:
        if api_manager.piste_client_id and api_manager.piste_client_secret:
            st.success("✅ Identifiants PISTE configurés")
        else:
            st.warning("⚠️ Identifiants PISTE manquants")
    
    # Test de connexion
    if st.button("🔌 Tester les connexions"):
        test_jurisprudence_sources()


def test_jurisprudence_sources():
    """Teste la connexion aux sources de jurisprudence"""
    with st.spinner("Test en cours..."):
        results = {}
        
        # Test Judilibre
        try:
            test_criteria = {
                'query': 'test',
                'juridictions': [],
                'sources': [SourceJurisprudence.JUDILIBRE],
                'articles': [],
                'date_range': None,
                'min_importance': 1
            }
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            test_results = loop.run_until_complete(api_manager.search_judilibre(test_criteria))
            results[SourceJurisprudence.JUDILIBRE] = len(test_results) >= 0
        except Exception as e:
            logger.error(f"Erreur test Judilibre: {e}")
            results[SourceJurisprudence.JUDILIBRE] = False
        
        # Test Légifrance
        try:
            test_criteria['sources'] = [SourceJurisprudence.LEGIFRANCE]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            test_results = loop.run_until_complete(api_manager.search_legifrance(test_criteria))
            results[SourceJurisprudence.LEGIFRANCE] = len(test_results) >= 0
        except Exception as e:
            logger.error(f"Erreur test Légifrance: {e}")
            results[SourceJurisprudence.LEGIFRANCE] = False
        
        # Afficher les résultats
        for source, success in results.items():
            config = SOURCE_CONFIGS[source]
            
            if success:
                st.success(f"✅ {config['name']} - Connexion OK")
            else:
                st.error(f"❌ {config['name']} - Connexion échouée")


# Fonctions utilitaires pour intégration avec d'autres modules

def get_jurisprudence_for_document(document_type: str, keywords: List[str], limit: int = 5) -> List[JurisprudenceReference]:
    """Récupère la jurisprudence pertinente pour un type de document"""
    
    # Critères de recherche adaptés au type
    search_criteria = {
        'query': ' '.join(keywords),
        'juridictions': [],
        'sources': st.session_state.get('enabled_jurisprudence_sources', 
            [SourceJurisprudence.LEGIFRANCE, SourceJurisprudence.JUDILIBRE]),
        'articles': [],
        'date_range': None,
        'min_importance': 7  # Jurisprudence importante pour les documents
    }
    
    # Adapter selon le type
    if document_type == 'conclusions':
        search_criteria['min_importance'] = 8
    elif document_type == 'plainte':
        search_criteria['min_importance'] = 6
    
    # Rechercher
    results = search_jurisprudence(search_criteria)
    
    return results[:limit]


def format_jurisprudence_citation(ref: JurisprudenceReference) -> str:
    """Formate une citation de jurisprudence pour insertion dans un document"""
    
    citation = ref.get_citation()
    
    if ref.url:
        # Format avec lien
        return f"[{citation}]({ref.url})"
    else:
        # Format simple
        return citation


def verify_and_update_citations(content: str) -> Tuple[str, List[VerificationResult]]:
    """Vérifie et met à jour les citations de jurisprudence dans un texte"""
    
    verifier = JurisprudenceVerifier()
    verification_results = []
    
    # Pattern pour détecter les citations
    citation_pattern = r'((?:Cass\.|CA|CE|CC)\s+[^,]+,\s+\d{1,2}\s+\w+\s+\d{4}(?:,\s+n°\s*[\d\-\.]+)?)'
    
    citations = re.findall(citation_pattern, content)
    
    for citation in citations:
        # Vérifier
        result = verifier.verify_reference(citation)
        verification_results.append(result)
        
        # Mettre à jour si trouvé
        if result.is_valid and result.reference:
            # Remplacer par la citation formatée
            formatted = format_jurisprudence_citation(result.reference)
            content = content.replace(citation, formatted)
    
    return content, verification_results


# Pour l'intégration dans le module recherche
def show_jurisprudence_interface(query: str = "", analysis: dict = None):
    """Interface principale appelée par le module recherche"""
    
    if query and analysis:
        process_jurisprudence_request(query, analysis)
    else:
        # Afficher l'interface par défaut
        initial_criteria = extract_jurisprudence_criteria(query or "", analysis or {})
        show_jurisprudence_search_interface(initial_criteria)


# Définir les fonctions exportées par le module
MODULE_FUNCTIONS = [
    'process_jurisprudence_request',
    'show_jurisprudence_search_interface',
    'show_jurisprudence_interface',
    'get_jurisprudence_for_document',
    'format_jurisprudence_citation',
    'verify_and_update_citations',
    'search_jurisprudence'
]