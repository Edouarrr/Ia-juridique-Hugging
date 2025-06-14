# managers/jurisprudence_verifier.py
"""
Gestionnaire de vérification et validation des jurisprudences
Vérifie automatiquement sur Judilibre et Légifrance
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote, urlencode

import aiohttp
import streamlit as st
from bs4 import BeautifulSoup
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

from config.app_config import LEGAL_APIS
from modules.jurisprudence_models import (JurisprudenceReference,
                                          SourceJurisprudence,
                                          VerificationResult)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JurisprudenceVerifier:
    """Vérifie et valide les jurisprudences sur les sources officielles"""
    
    def __init__(self):
        self.session = None
        self.verified_cache = TTLCache(maxsize=1000, ttl=3600)  # Cache 1h
        self.legifrance_token = None
        self.token_expiry = None
        self.judilibre_config = LEGAL_APIS["judilibre"]
        self.legifrance_config = LEGAL_APIS["legifrance"]
        
    async def __aenter__(self):
        """Initialise la session aiohttp"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session"""
        if self.session:
            await self.session.close()
            
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
                else:
                    logger.error(f"Erreur OAuth Légifrance: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Erreur obtention token Légifrance: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_judilibre(self, reference: JurisprudenceReference) -> Optional[Dict]:
        """Recherche sur Judilibre avec retry automatique"""
        if not self.judilibre_config['enabled']:
            return None
            
        headers = {
            'KeyId': self.judilibre_config['api_key'],
            'Accept': 'application/json'
        }
        
        # Construire la requête
        params = {
            'query': reference.to_search_query(),
            'field': ['numero', 'date_creation', 'sommaire', 'texte_integral'],
            'size': 10,
            'sort': 'pertinence'
        }
        
        try:
            url = f"{self.judilibre_config['base_url']}{self.judilibre_config['endpoints']['search']}"
            async with self.session.get(url, headers=headers, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Analyser les résultats
                    for result in data.get('results', []):
                        if self._match_decision(result, reference):
                            return {
                                'found': True,
                                'source': 'judilibre',
                                'url': f"https://www.courdecassation.fr/decision/{result['id']}",
                                'sommaire': result.get('sommaire'),
                                'texte': result.get('texte_integral'),
                                'score': result.get('score', 1.0),
                                'data': result
                            }
                    return None
                else:
                    logger.error(f"Erreur Judilibre: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error("Timeout Judilibre")
            return None
        except Exception as e:
            logger.error(f"Erreur recherche Judilibre: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_legifrance(self, reference: JurisprudenceReference) -> Optional[Dict]:
        """Recherche sur Légifrance avec retry automatique"""
        if not self.legifrance_config['enabled']:
            return None
            
        token = await self.get_legifrance_token()
        if not token:
            return None
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Adapter la requête au format Légifrance
        search_data = {
            'fond': 'JURI',
            'recherche': {
                'typeRecherche': 'exacte',
                'mots': reference.to_search_query(),
                'champRecherche': 'ALL',
                'operateur': 'ET'
            },
            'nbResultat': 10
        }
        
        try:
            url = f"{self.legifrance_config['base_url']}{self.legifrance_config['endpoints']['search']}"
            async with self.session.post(
                url, 
                headers=headers, 
                json=search_data,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parcourir les résultats
                    for result in data.get('results', []):
                        if self._match_legifrance(result, reference):
                            return {
                                'found': True,
                                'source': 'legifrance',
                                'url': f"https://www.legifrance.gouv.fr/juri/id/{result['id']}",
                                'sommaire': result.get('titre'),
                                'texte': result.get('texte'),
                                'score': result.get('pertinence', 1.0),
                                'data': result
                            }
                    return None
                else:
                    logger.error(f"Erreur Légifrance: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error("Timeout Légifrance")
            return None
        except Exception as e:
            logger.error(f"Erreur recherche Légifrance: {e}")
            return None
    
    def _match_decision(self, result: Dict, reference: JurisprudenceReference) -> bool:
        """Vérifie si un résultat correspond à la référence avec tolérance"""
        # Extraire et nettoyer les numéros
        result_numero = re.sub(r'[^\d\-.]', '', result.get('numero', ''))
        ref_numero = re.sub(r'[^\d\-.]', '', reference.numero)
        
        # Comparaison flexible des numéros
        if self._similar_numbers(ref_numero, result_numero):
            return True
            
        # Vérifier la date si disponible
        if 'date_creation' in result:
            if self._similar_dates(reference.date, result['date_creation']):
                # Si les dates correspondent, vérifier la juridiction
                if self._similar_juridiction(reference.juridiction, result.get('juridiction', '')):
                    return True
                    
        return False
    
    def _match_legifrance(self, item: Dict, reference: JurisprudenceReference) -> bool:
        """Vérifie la correspondance pour Légifrance"""
        titre = item.get('titre', '').lower()
        ref_numero = re.sub(r'[^\d\-.]', '', reference.numero).lower()
        
        # Recherche du numéro dans le titre ou le texte
        if ref_numero in titre:
            return True
            
        # Vérification dans les métadonnées
        if 'numero' in item:
            item_numero = re.sub(r'[^\d\-.]', '', item['numero'])
            if self._similar_numbers(ref_numero, item_numero):
                return True
                
        return False
    
    def _similar_numbers(self, num1: str, num2: str) -> bool:
        """Compare deux numéros de pourvoi avec tolérance"""
        # Nettoyer les numéros
        clean1 = re.sub(r'[^\d]', '', num1)
        clean2 = re.sub(r'[^\d]', '', num2)
        
        # Comparaison exacte
        if clean1 == clean2:
            return True
            
        # Tolérance pour les variations mineures
        if len(clean1) >= 6 and len(clean2) >= 6:
            # Comparer les 6 premiers chiffres significatifs
            return clean1[:6] == clean2[:6]
            
        return False
    
    def _similar_dates(self, date1: str, date2: str) -> bool:
        """Compare deux dates avec tolérance"""
        # Extraire l'année
        year1 = re.search(r'\d{4}', date1)
        year2 = re.search(r'\d{4}', date2)
        
        if year1 and year2:
            return year1.group() == year2.group()
        return False
    
    def _similar_juridiction(self, jur1: str, jur2: str) -> bool:
        """Compare deux juridictions"""
        # Normaliser
        norm1 = jur1.lower().replace('.', '').replace(' ', '')
        norm2 = jur2.lower().replace('.', '').replace(' ', '')
        
        return norm1 in norm2 or norm2 in norm1
    
    async def verify_reference(self, reference: JurisprudenceReference) -> VerificationResult:
        """Vérifie une référence sur toutes les sources"""
        # Vérifier le cache
        cache_key = reference.to_citation()
        if cache_key in self.verified_cache:
            return self.verified_cache[cache_key]
        
        # Recherches parallèles
        tasks = []
        sources_checked = []
        
        if self.judilibre_config['enabled']:
            tasks.append(self.search_judilibre(reference))
            sources_checked.append(SourceJurisprudence.JUDILIBRE)
            
        if self.legifrance_config['enabled']:
            tasks.append(self.search_legifrance(reference))
            sources_checked.append(SourceJurisprudence.LEGIFRANCE)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyser les résultats
        matches = []
        found = False
        confidence = 0.0
        
        for i, result in enumerate(results):
            if isinstance(result, dict) and result and result.get('found'):
                matches.append(result)
                found = True
                confidence = max(confidence, result.get('score', 0.8))
                reference.found_on.append(result['source'])
                if not reference.url_source:
                    reference.url_source = result['url']
                if result.get('sommaire') and not reference.sommaire:
                    reference.sommaire = result['sommaire']
        
        # Créer le résultat de vérification
        verification_result = VerificationResult(
            reference=reference,
            status='verified' if found else 'not_found',
            confidence=confidence,
            sources_checked=sources_checked,
            matches=matches
        )
        
        # Mettre à jour la référence
        reference.verified = found
        reference.verification_date = datetime.now()
        
        # Mettre en cache
        self.verified_cache[cache_key] = verification_result
        
        return verification_result
    
    async def verify_multiple_references(
        self, 
        references: List[JurisprudenceReference],
        progress_callback=None
    ) -> List[VerificationResult]:
        """Vérifie plusieurs références avec progression"""
        results = []
        
        # Traiter par batch pour optimiser
        batch_size = 5
        for i in range(0, len(references), batch_size):
            batch = references[i:i+batch_size]
            batch_results = await asyncio.gather(
                *[self.verify_reference(ref) for ref in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, VerificationResult):
                    results.append(result)
                else:
                    logger.error(f"Erreur vérification: {result}")
                    
            if progress_callback:
                progress_callback(min(i + batch_size, len(references)), len(references))
                
        return results
    
    def extract_references_from_text(self, text: str) -> List[JurisprudenceReference]:
        """Extrait les références de jurisprudence d'un texte avec patterns améliorés"""
        references = []
        
        # Patterns de reconnaissance améliorés
        patterns = [
            # Cour de cassation - format standard
            r'(Cass\.?\s*(?:civ|crim|com|soc)\.?)\s*,?\s*(\d{1,2}\s+\w+\s+\d{4})\s*,?\s*n°\s*([\d\-\.]+)',
            # Cour de cassation - format alternatif
            r'(Cour de cassation),?\s*(?:chambre\s+)?(\w+),?\s*(\d{1,2}\s+\w+\s+\d{4}),?\s*(?:n°|pourvoi)\s*([\d\-\.]+)',
            # Conseil d'État
            r'(C\.?E\.?|Conseil d\'État),?\s*(\d{1,2}\s+\w+\s+\d{4}),?\s*n°\s*(\d+)',
            # Conseil constitutionnel
            r'(Cons\.?\s*const\.?|Conseil constitutionnel),?\s*(?:décision\s*)?(\d{1,2}\s+\w+\s+\d{4}),?\s*n°\s*([\d\-]+\s*(?:DC|QPC))',
            # Cour d'appel
            r'(CA|C\.A\.|Cour d\'appel)\s+(?:de\s+)?(\w+),?\s*(\d{1,2}\s+\w+\s+\d{4}),?\s*n°\s*([\d/\-]+)',
            # Format avec date numérique
            r'((?:Cass|CE|CA)[\w\s\.]+?),?\s*(\d{1,2}[\s\-/]\d{1,2}[\s\-/]\d{4}),?\s*(?:n°|pourvoi)\s*([\d\-\.]+)',
            # CJUE et CEDH
            r'(CJUE|CEDH|Cour EDH),?\s*(\d{1,2}\s+\w+\s+\d{4}),?\s*(?:aff\.|affaire|n°)\s*([\w\-/]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    juridiction = match.group(1).strip()
                    date = match.group(2).strip()
                    numero = match.group(3).strip()
                    
                    # Normaliser la juridiction
                    juridiction = self._normalize_juridiction(juridiction)
                    
                    # Créer la référence
                    ref = JurisprudenceReference(
                        juridiction=juridiction,
                        date=date,
                        numero=numero,
                        ai_proposed=True
                    )
                    
                    references.append(ref)
                except Exception as e:
                    logger.warning(f"Erreur extraction référence: {e}")
        
        # Dédupliquer
        unique_refs = []
        seen = set()
        for ref in references:
            key = ref.to_citation()
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)
                
        return unique_refs
    
    def _normalize_juridiction(self, juridiction: str) -> str:
        """Normalise les noms de juridiction"""
        juridiction = juridiction.strip()
        
        # Mapping complet des abréviations
        mappings = {
            # Cour de cassation
            'cass': 'Cass.',
            'cassation': 'Cass.',
            'cour de cassation': 'Cass.',
            # Chambres
            'civ': 'civ.',
            'civile': 'civ.',
            'crim': 'crim.',
            'criminelle': 'crim.',
            'com': 'com.',
            'commerciale': 'com.',
            'soc': 'soc.',
            'sociale': 'soc.',
            # Conseil d'État
            'ce': 'CE',
            'c.e.': 'CE',
            'conseil detat': 'CE',
            "conseil d'état": 'CE',
            # Autres
            'ca': 'CA',
            'c.a.': 'CA',
            "cour d'appel": 'CA',
            'cons const': 'Cons. const.',
            'conseil constitutionnel': 'Cons. const.',
            'cjue': 'CJUE',
            'cedh': 'CEDH',
            'cour edh': 'CEDH'
        }
        
        juridiction_lower = juridiction.lower()
        
        # Recherche exacte d'abord
        if juridiction_lower in mappings:
            return mappings[juridiction_lower]
        
        # Recherche par préfixe
        for abbr, normalized in mappings.items():
            if juridiction_lower.startswith(abbr):
                rest = juridiction[len(abbr):].strip()
                if rest and normalized == 'Cass.':
                    # Garder la chambre pour la Cour de cassation
                    return f"{normalized} {rest}"
                elif rest and normalized == 'CA':
                    # Garder la ville pour la Cour d'appel
                    return f"{normalized} {rest.title()}"
                return normalized
                
        return juridiction

# Fonctions d'aide pour l'intégration Streamlit
def display_jurisprudence_verification(text: str, verifier: JurisprudenceVerifier):
    """Affiche les jurisprudences extraites avec leur statut de vérification"""
    
    st.markdown("### 🔍 Vérification des jurisprudences citées")
    
    # Extraire les références
    references = verifier.extract_references_from_text(text)
    
    if not references:
        st.info("Aucune référence de jurisprudence détectée dans le texte.")
        return []
    
    st.info(f"📚 {len(references)} références détectées. Vérification en cours...")
    
    # Barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Vérifier les références
    async def verify_all():
        results = []
        async with verifier:
            for i, ref in enumerate(references):
                status_text.text(f"Vérification de {ref.to_citation()}...")
                result = await verifier.verify_reference(ref)
                results.append(result)
                progress_bar.progress((i + 1) / len(references))
        return results
    
    # Exécuter la vérification
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    verification_results = loop.run_until_complete(verify_all())
    
    # Effacer la barre de progression
    progress_bar.empty()
    status_text.empty()
    
    # Afficher les résultats
    col1, col2 = st.columns([3, 1])
    
    verified_count = sum(1 for r in verification_results if r.status == 'verified')
    
    with col1:
        st.markdown(f"**Résultats:** {verified_count}/{len(verification_results)} références vérifiées")
    
    with col2:
        if st.button("📥 Exporter", key="export_juris"):
            report = create_verification_report(verification_results)
            st.download_button(
                "Télécharger le rapport",
                report,
                "rapport_jurisprudences.txt",
                "text/plain"
            )
    
    # Tableau des résultats
    for result in verification_results:
        ref = result.reference
        with st.container():
            cols = st.columns([4, 1, 1])
            
            with cols[0]:
                if result.status == 'verified':
                    st.markdown(f"✅ **{ref.to_citation()}**")
                    if ref.url_source:
                        st.caption(f"[Consulter la décision]({ref.url_source})")
                else:
                    st.markdown(f"❌ ~~{ref.to_citation()}~~")
                    st.caption("Non trouvée dans les bases officielles")
            
            with cols[1]:
                if ref.found_on:
                    sources = ", ".join(ref.found_on)
                    st.caption(f"📍 {sources}")
            
            with cols[2]:
                if result.status == 'verified' and ref.sommaire:
                    if st.button("📄", key=f"sommaire_{ref.numero}", help="Voir le sommaire"):
                        st.info(ref.sommaire)
    
    return verification_results

def create_verification_report(results: List[VerificationResult]) -> str:
    """Crée un rapport détaillé de vérification"""
    report = "RAPPORT DE VÉRIFICATION DES JURISPRUDENCES\n"
    report += "=" * 50 + "\n\n"
    report += f"Date de vérification: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    verified = [r for r in results if r.status == 'verified']
    not_found = [r for r in results if r.status == 'not_found']
    
    report += f"RÉSUMÉ\n"
    report += f"- Total des références: {len(results)}\n"
    report += f"- Vérifiées: {len(verified)} ({len(verified)/len(results)*100:.1f}%)\n"
    report += f"- Non trouvées: {len(not_found)} ({len(not_found)/len(results)*100:.1f}%)\n\n"
    
    if verified:
        report += "RÉFÉRENCES VÉRIFIÉES\n"
        report += "-" * 30 + "\n"
        for result in verified:
            ref = result.reference
            report += f"\n{ref.to_citation()}\n"
            report += f"Sources: {', '.join(ref.found_on)}\n"
            report += f"Confiance: {result.confidence:.0%}\n"
            if ref.url_source:
                report += f"URL: {ref.url_source}\n"
    
    if not_found:
        report += "\n\nRÉFÉRENCES NON TROUVÉES\n"
        report += "-" * 30 + "\n"
        for result in not_found:
            ref = result.reference
            report += f"\n{ref.to_citation()}\n"
            report += "⚠️ Cette référence n'a pas pu être vérifiée dans les bases officielles\n"
            report += f"Sources consultées: {', '.join([s.value for s in result.sources_checked])}\n"
    
    return report

# Export pour intégration
__all__ = [
    'JurisprudenceVerifier',
    'display_jurisprudence_verification',
    'create_verification_report'
]