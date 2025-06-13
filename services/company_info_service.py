"""Service unifié pour la récupération et l'enrichissement des informations d'entreprises"""

import os
import json
import re
import asyncio
import requests
import httpx
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from bs4 import BeautifulSoup
import streamlit as st

# Configuration
PAPPERS_API_KEY = os.getenv('PAPPERS_API_KEY') or st.secrets.get("PAPPERS_API_KEY", "")
PAPPERS_BASE_URL = "https://api.pappers.fr/v2"
CACHE_DURATION = timedelta(days=7)

# ========================= STRUCTURES DE DONNÉES =========================

@dataclass
class InfosSociete:
    """Informations enrichies d'une société"""
    nom: str
    siren: str
    forme_juridique: str
    siege_social: str
    code_postal: str
    ville: str
    capital_social: Optional[int] = None
    date_creation: Optional[str] = None
    statut: str = "Active"
    dirigeants: List[Dict[str, str]] = None
    activite: Optional[str] = None
    code_naf: Optional[str] = None
    effectif: Optional[str] = None
    chiffre_affaires: Optional[int] = None
    resultat: Optional[int] = None
    date_derniers_comptes: Optional[str] = None
    siret: Optional[str] = None
    rcs_numero: Optional[str] = None
    rcs_ville: Optional[str] = None
    source: str = "Pappers"
    date_recuperation: Optional[datetime] = None
    representants_legaux: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.dirigeants is None:
            self.dirigeants = []
        if self.representants_legaux is None:
            self.representants_legaux = []
        if self.date_recuperation is None:
            self.date_recuperation = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour l'export"""
        return {
            'nom': self.nom,
            'siren': self.siren,
            'siret': self.siret,
            'forme_juridique': self.forme_juridique,
            'siege_social': self.siege_social,
            'code_postal': self.code_postal,
            'ville': self.ville,
            'capital_social': self.capital_social,
            'date_creation': self.date_creation,
            'statut': self.statut,
            'dirigeants': self.dirigeants,
            'representants_legaux': self.representants_legaux,
            'activite': self.activite,
            'code_naf': self.code_naf,
            'effectif': self.effectif,
            'chiffre_affaires': self.chiffre_affaires,
            'resultat': self.resultat,
            'date_derniers_comptes': self.date_derniers_comptes,
            'rcs_numero': self.rcs_numero,
            'rcs_ville': self.rcs_ville,
            'source': self.source,
            'date_recuperation': self.date_recuperation.isoformat() if self.date_recuperation else None
        }
    
    def format_for_acte(self) -> str:
        """Formate les informations pour un acte juridique"""
        lines = [
            f"{self.nom}",
            f"{self.forme_juridique}",
            f"SIREN : {self.siren}",
            f"Siège social : {self.siege_social}",
            f"{self.code_postal} {self.ville}"
        ]
        
        if self.capital_social:
            lines.append(f"Capital social : {self.capital_social:,} €".replace(',', ' '))
        
        if self.rcs_numero and self.rcs_ville:
            lines.append(f"RCS {self.rcs_ville} {self.rcs_numero}")
        
        if self.dirigeants or self.representants_legaux:
            lines.append("Représentée par :")
            # Prioriser dirigeants puis representants_legaux
            all_representants = self.dirigeants[:2] if self.dirigeants else []
            if not all_representants and self.representants_legaux:
                all_representants = self.representants_legaux[:2]
            
            for rep in all_representants:
                if isinstance(rep, dict):
                    nom = rep.get('nom', '')
                    qualite = rep.get('qualite', '')
                    lines.append(f"- {qualite}: {nom}" if qualite else f"- {nom}")
        
        return '\n'.join(lines)
    
    def format_for_legal_document(self) -> str:
        """Format condensé pour document juridique"""
        parts = [self.nom]
        
        if self.forme_juridique:
            parts.append(f", {self.forme_juridique}")
        
        if self.capital_social:
            parts.append(f" au capital de {self.capital_social:,} €".replace(',', ' '))
        
        if self.rcs_numero and self.rcs_ville:
            parts.append(f", immatriculée au RCS de {self.rcs_ville} sous le numéro {self.rcs_numero}")
        elif self.siren:
            parts.append(f", SIREN {self.siren}")
        
        if self.siege_social:
            parts.append(f", dont le siège social est situé {self.siege_social}")
            if self.code_postal and self.ville:
                parts.append(f", {self.code_postal} {self.ville}")
        
        if self.dirigeants or self.representants_legaux:
            rep = (self.dirigeants or self.representants_legaux)[0]
            if isinstance(rep, dict):
                parts.append(f", représentée par {rep.get('nom', '')}")
                if rep.get('qualite'):
                    parts.append(f" en sa qualité de {rep['qualite']}")
        
        return "".join(parts)

# ========================= CACHE LOCAL =========================

class CacheSocietes:
    """Cache local pour éviter les appels API répétés"""
    
    def __init__(self):
        self.cache_file = "cache_societes.json"
        self.memory_cache = {}
        self.file_cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Charge le cache depuis le fichier"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Sauvegarde le cache dans le fichier"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde cache: {e}")
    
    def get(self, key: str) -> Optional[Dict]:
        """Récupère une entrée du cache si elle est valide"""
        # Vérifier d'abord le cache mémoire
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Ensuite le cache fichier
        if key in self.file_cache:
            entry = self.file_cache[key]
            if 'timestamp' in entry:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                if datetime.now() - timestamp < CACHE_DURATION:
                    # Mettre en cache mémoire pour accès plus rapide
                    self.memory_cache[key] = entry.get('data')
                    return entry.get('data')
        return None
    
    def set(self, key: str, data: Dict):
        """Ajoute une entrée au cache"""
        entry = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self.memory_cache[key] = data
        self.file_cache[key] = entry
        self._save_cache()

# ========================= SERVICE PRINCIPAL =========================

class CompanyInfoService:
    """Service unifié pour récupérer les informations d'entreprises"""
    
    def __init__(self):
        self.pappers_api_key = PAPPERS_API_KEY
        self.cache = CacheSocietes()
        self.sync_session = requests.Session()
        self.sync_session.headers.update({'User-Agent': 'Assistant-Juridique/1.0'})
        self.async_session = None
        self._init_async_session()
    
    def _init_async_session(self):
        """Initialise la session async si nécessaire"""
        try:
            self.async_session = httpx.AsyncClient(timeout=30.0)
        except:
            pass
    
    # ===== MÉTHODES SYNCHRONES (compatibilité avec l'ancien code) =====
    
    def search_entreprise(self, query: str) -> List[InfosSociete]:
        """Recherche synchrone d'entreprise (compatibilité)"""
        cache_key = f"search_{query.lower()}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return [self._dict_to_infos_societe(e) for e in cached_result]
        
        if not self.pappers_api_key:
            return self._fallback_search(query)
        
        try:
            params = {
                'api_token': self.pappers_api_key,
                'q': query,
                'page': 1,
                'par_page': 5
            }
            
            response = self.sync_session.get(
                f"{PAPPERS_BASE_URL}/entreprise/recherche",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                resultats = data.get('resultats', [])
                self.cache.set(cache_key, resultats)
                return [self._parse_entreprise(e) for e in resultats]
            else:
                return self._fallback_search(query)
                
        except Exception as e:
            print(f"Erreur recherche Pappers: {e}")
            return self._fallback_search(query)
    
    def get_entreprise_by_siren(self, siren: str) -> Optional[InfosSociete]:
        """Récupère les informations par SIREN (synchrone)"""
        siren = siren.replace(' ', '').replace('.', '')
        
        cache_key = f"siren_{siren}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return self._parse_entreprise(cached_result)
        
        if not self.pappers_api_key:
            return None
        
        try:
            params = {
                'api_token': self.pappers_api_key,
                'siren': siren
            }
            
            response = self.sync_session.get(
                f"{PAPPERS_BASE_URL}/entreprise",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.cache.set(cache_key, data)
                return self._parse_entreprise(data)
            
        except Exception as e:
            print(f"Erreur récupération SIREN: {e}")
        
        return None
    
    # ===== MÉTHODES ASYNCHRONES =====
    
    async def get_company_info(self, company_name: str, 
                             try_societe_com: bool = True) -> Optional[InfosSociete]:
        """
        Récupère les informations d'une entreprise (async)
        
        Args:
            company_name: Nom de l'entreprise
            try_societe_com: Essayer Societe.com si Pappers échoue
            
        Returns:
            InfosSociete ou None
        """
        # Essayer Pappers d'abord
        info = await self._fetch_from_pappers_async(company_name)
        
        # Si échec et option activée, essayer Societe.com
        if not info and try_societe_com:
            info = await self._fetch_from_societe_com(company_name)
        
        return info
    
    async def _fetch_from_pappers_async(self, company_name: str) -> Optional[InfosSociete]:
        """Récupère depuis Pappers en async"""
        if not self.pappers_api_key or not self.async_session:
            return None
        
        cache_key = f"async_search_{company_name.lower()}"
        cached = self.cache.get(cache_key)
        if cached:
            return self._dict_to_infos_societe(cached)
        
        try:
            search_params = {
                "q": company_name,
                "api_token": self.pappers_api_key,
                "par_page": 5
            }
            
            response = await self.async_session.get(
                f"{PAPPERS_BASE_URL}/recherche",
                params=search_params
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("resultats"):
                return None
            
            company = data["resultats"][0]
            
            # Récupérer les détails si SIREN disponible
            if company.get("siren"):
                detail_params = {
                    "siren": company["siren"],
                    "api_token": self.pappers_api_key
                }
                detail_response = await self.async_session.get(
                    f"{PAPPERS_BASE_URL}/entreprise",
                    params=detail_params
                )
                if detail_response.status_code == 200:
                    company = detail_response.json()
            
            info = self._parse_entreprise(company)
            self.cache.set(cache_key, info.to_dict())
            return info
            
        except Exception as e:
            print(f"Erreur Pappers async: {e}")
            return None
    
    async def _fetch_from_societe_com(self, company_name: str) -> Optional[InfosSociete]:
        """Récupère depuis Societe.com par scraping"""
        if not self.async_session:
            return None
        
        try:
            search_url = f"https://www.societe.com/cgi-bin/search"
            search_params = {"champs": company_name}
            
            response = await self.async_session.get(
                search_url, 
                params=search_params, 
                follow_redirects=True
            )
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver le premier résultat
            result_link = soup.select_one("div.result a")
            if not result_link:
                return None
            
            # Accéder à la page de l'entreprise
            company_url = f"https://www.societe.com{result_link['href']}"
            company_response = await self.async_session.get(company_url)
            
            if company_response.status_code != 200:
                return None
            
            return self._parse_societe_com_page(company_response.text)
            
        except Exception as e:
            print(f"Erreur Societe.com: {e}")
            return None
    
    def _parse_societe_com_page(self, html_content: str) -> Optional[InfosSociete]:
        """Parse une page Societe.com"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialiser avec des valeurs par défaut
        info_dict = {
            'source': 'Societe.com',
            'statut': 'Active'
        }
        
        # Titre = nom de l'entreprise
        title = soup.select_one("h1")
        if title:
            info_dict['nom'] = title.text.strip()
        else:
            return None
        
        # Table d'identité
        identity_table = soup.select_one("table#identite")
        if identity_table:
            rows = identity_table.select("tr")
            for row in rows:
                cells = row.select("td")
                if len(cells) >= 2:
                    label = cells[0].text.strip().lower()
                    value = cells[1].text.strip()
                    
                    if "siren" in label:
                        info_dict['siren'] = value.replace(" ", "")
                    elif "siret" in label:
                        info_dict['siret'] = value.replace(" ", "")
                    elif "forme juridique" in label:
                        info_dict['forme_juridique'] = value
                    elif "capital social" in label:
                        info_dict['capital_social'] = self._parse_capital(value)
                    elif "adresse" in label:
                        info_dict['siege_social'] = value
                    elif "ville" in label:
                        info_dict['ville'] = value
                    elif "code postal" in label:
                        info_dict['code_postal'] = value
                    elif "rcs" in label:
                        parts = value.split()
                        if len(parts) >= 2:
                            info_dict['rcs_ville'] = parts[0]
                            info_dict['rcs_numero'] = " ".join(parts[1:])
                    elif "ape" in label or "naf" in label:
                        info_dict['code_naf'] = value.split()[0] if value else ""
                        info_dict['activite'] = " ".join(value.split()[1:]) if len(value.split()) > 1 else ""
                    elif "création" in label:
                        info_dict['date_creation'] = value
                    elif "effectif" in label:
                        info_dict['effectif'] = value
        
        # Dirigeants
        dirigeants = []
        dirigeants_section = soup.select("div#dirigeants")
        if dirigeants_section:
            for dirigeant in dirigeants_section[0].select("div.dirigeant"):
                nom_elem = dirigeant.select_one("a")
                qualite_elem = dirigeant.select_one("span.qualite")
                if nom_elem:
                    dirigeants.append({
                        "nom": nom_elem.text.strip(),
                        "qualite": qualite_elem.text.strip() if qualite_elem else ""
                    })
        
        info_dict['dirigeants'] = dirigeants
        info_dict['representants_legaux'] = dirigeants  # Compatibilité
        
        # Créer l'objet InfosSociete
        return InfosSociete(**self._clean_dict_for_dataclass(info_dict))
    
    # ===== MÉTHODES DE PARSING ET UTILITAIRES =====
    
    def _parse_entreprise(self, data: Dict) -> InfosSociete:
        """Parse les données Pappers en InfosSociete"""
        # Informations de base
        nom = data.get('denomination', data.get('nom_entreprise', 'Non renseigné'))
        siren = data.get('siren', '')
        forme_juridique = data.get('forme_juridique', '')
        
        # Siège social
        siege = data.get('siege', {})
        adresse = self._format_address(siege)
        code_postal = siege.get('code_postal', '')
        ville = siege.get('ville', '')
        
        # Capital
        capital = data.get('capital', {})
        capital_social = None
        if capital and isinstance(capital, dict):
            capital_social = capital.get('montant')
        
        # Dirigeants
        dirigeants = []
        representants = data.get('representants', [])
        for rep in representants[:3]:
            nom_complet = f"{rep.get('prenom', '')} {rep.get('nom', '')}".strip()
            if not nom_complet:
                nom_complet = rep.get('nom_complet', '')
            
            dirigeant = {
                'nom': nom_complet,
                'qualite': rep.get('qualite', ''),
                'date_prise_poste': rep.get('date_prise_poste', '')
            }
            dirigeants.append(dirigeant)
        
        # Autres informations
        return InfosSociete(
            nom=nom,
            siren=siren,
            siret=siege.get('siret', ''),
            forme_juridique=forme_juridique,
            siege_social=adresse,
            code_postal=code_postal,
            ville=ville,
            capital_social=capital_social,
            date_creation=data.get('date_creation'),
            dirigeants=dirigeants,
            representants_legaux=dirigeants,
            activite=data.get('libelle_code_naf', ''),
            code_naf=data.get('code_naf', ''),
            effectif=data.get('tranche_effectif', ''),
            chiffre_affaires=self._get_latest_finance(data, 'chiffre_affaires'),
            resultat=self._get_latest_finance(data, 'resultat'),
            date_derniers_comptes=self._get_latest_finance(data, 'date_cloture'),
            rcs_numero=data.get('numero_rcs', ''),
            rcs_ville=data.get('greffe', ''),
            source='Pappers'
        )
    
    def _get_latest_finance(self, data: Dict, field: str) -> Optional[Any]:
        """Récupère la dernière donnée financière disponible"""
        finances = data.get('finances', [])
        if finances and isinstance(finances, list) and len(finances) > 0:
            return finances[0].get(field)
        return None
    
    def _format_address(self, siege_data: Dict) -> str:
        """Formate une adresse depuis les données siege"""
        if not siege_data:
            return ""
        
        parts = []
        if siege_data.get("numero_voie"):
            parts.append(siege_data["numero_voie"])
        if siege_data.get("type_voie"):
            parts.append(siege_data["type_voie"])
        if siege_data.get("libelle_voie"):
            parts.append(siege_data["libelle_voie"])
        
        return " ".join(parts)
    
    def _parse_capital(self, capital_str: str) -> Optional[int]:
        """Parse un montant de capital"""
        if not capital_str:
            return None
        
        # Nettoyer et extraire les chiffres
        capital_str = capital_str.replace(" ", "").replace(",", "").replace("€", "")
        match = re.search(r'(\d+)', capital_str)
        if match:
            return int(match.group(1))
        return None
    
    def _fallback_search(self, query: str) -> List[InfosSociete]:
        """Recherche de secours sans API"""
        return [InfosSociete(
            nom=query,
            siren="[À VÉRIFIER]",
            forme_juridique="[À VÉRIFIER]",
            siege_social="[À VÉRIFIER]",
            code_postal="[À VÉRIFIER]",
            ville="[À VÉRIFIER]"
        )]
    
    def _dict_to_infos_societe(self, data: Dict) -> InfosSociete:
        """Convertit un dict en InfosSociete"""
        # Nettoyer le dict pour ne garder que les champs valides
        cleaned = self._clean_dict_for_dataclass(data)
        return InfosSociete(**cleaned)
    
    def _clean_dict_for_dataclass(self, data: Dict) -> Dict:
        """Nettoie un dict pour qu'il corresponde aux champs de InfosSociete"""
        valid_fields = {
            'nom', 'siren', 'siret', 'forme_juridique', 'siege_social',
            'code_postal', 'ville', 'capital_social', 'date_creation',
            'statut', 'dirigeants', 'representants_legaux', 'activite',
            'code_naf', 'effectif', 'chiffre_affaires', 'resultat',
            'date_derniers_comptes', 'rcs_numero', 'rcs_ville', 'source'
        }
        
        cleaned = {}
        for key, value in data.items():
            if key in valid_fields:
                cleaned[key] = value
        
        # Valeurs par défaut obligatoires
        required = ['nom', 'siren', 'forme_juridique', 'siege_social', 'code_postal', 'ville']
        for field in required:
            if field not in cleaned:
                cleaned[field] = ''
        
        return cleaned
    
    # ===== MÉTHODES D'ENRICHISSEMENT =====
    
    async def enrichir_parties(self, parties: List[str]) -> List[Dict[str, Any]]:
        """Enrichit une liste de parties avec leurs informations"""
        parties_enrichies = []
        
        for partie in parties:
            if not partie or len(partie) < 3:
                continue
            
            # Nettoyer le nom
            partie_clean = self._nettoyer_nom_partie(partie)
            
            # Rechercher
            info = await self.get_company_info(partie_clean)
            
            if info:
                parties_enrichies.append({
                    'nom_original': partie,
                    'nom_societe': info.nom,
                    'siren': info.siren,
                    'forme_juridique': info.forme_juridique,
                    'siege_social': info.siege_social,
                    'code_postal': info.code_postal,
                    'ville': info.ville,
                    'capital_social': info.capital_social,
                    'dirigeants': info.dirigeants,
                    'activite': info.activite,
                    'infos_completes': info
                })
            else:
                parties_enrichies.append({
                    'nom_original': partie,
                    'nom_societe': partie,
                    'non_trouve': True
                })
        
        return parties_enrichies
    
    def _nettoyer_nom_partie(self, nom: str) -> str:
        """Nettoie un nom de partie pour la recherche"""
        # Enlever les mentions entre parenthèses
        nom = re.sub(r'\([^)]*\)', '', nom)
        
        # Enlever les formes juridiques courantes
        formes = ['SAS', 'SARL', 'SA', 'SCI', 'EURL', 'SASU', 'SNC']
        for forme in formes:
            if nom.upper().endswith(' ' + forme):
                nom = nom[:-len(forme)-1]
        
        return nom.strip()
    
    async def close(self):
        """Ferme les sessions"""
        if self.async_session:
            await self.async_session.aclose()

# ===== FONCTIONS D'INTERFACE ET HELPERS =====

def show_enrichissement_interface():
    """Interface Streamlit pour tester l'enrichissement"""
    st.header("🏢 Enrichissement des informations sociétés")
    
    if not PAPPERS_API_KEY:
        st.warning("""
        ⚠️ API Pappers non configurée
        
        Pour activer l'enrichissement automatique :
        1. Obtenez une clé API sur [pappers.fr](https://www.pappers.fr/api)
        2. Ajoutez la variable d'environnement : `PAPPERS_API_KEY=votre_cle`
        """)
        st.info("Mode dégradé activé - Possibilité de rechercher sur Societe.com")
    else:
        st.success("✅ API Pappers configurée")
    
    # Zone de test
    st.subheader("🔍 Tester la recherche")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Nom ou SIREN de la société",
            placeholder="Ex: Vinci, 552037806"
        )
    with col2:
        source = st.selectbox(
            "Source",
            ["Pappers", "Societe.com", "Auto"]
        )
    
    if st.button("Rechercher", type="primary"):
        if query:
            with st.spinner("Recherche en cours..."):
                service = CompanyInfoService()
                
                # Recherche selon la source
                if source == "Auto" or source == "Pappers":
                    resultats = service.search_entreprise(query)
                else:
                    # Mode async pour Societe.com
                    import asyncio
                    async def search_societe():
                        return await service._fetch_from_societe_com(query)
                    
                    info = asyncio.run(search_societe())
                    resultats = [info] if info else []
                
                if resultats:
                    st.success(f"✅ {len(resultats)} résultat(s) trouvé(s)")
                    
                    for i, societe in enumerate(resultats, 1):
                        with st.expander(f"{i}. {societe.nom} - {societe.siren}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Informations générales**")
                                st.write(f"• Forme juridique: {societe.forme_juridique}")
                                st.write(f"• Siège: {societe.siege_social}")
                                st.write(f"• {societe.code_postal} {societe.ville}")
                                if societe.capital_social:
                                    st.write(f"• Capital: {societe.capital_social:,} €".replace(',', ' '))
                                if societe.rcs_numero:
                                    st.write(f"• RCS: {societe.rcs_ville} {societe.rcs_numero}")
                            
                            with col2:
                                st.markdown("**Activité**")
                                if societe.activite:
                                    st.write(f"• {societe.activite}")
                                if societe.effectif:
                                    st.write(f"• Effectif: {societe.effectif}")
                                if societe.dirigeants:
                                    st.markdown("**Dirigeants:**")
                                    for d in societe.dirigeants[:3]:
                                        st.write(f"• {d['qualite']}: {d['nom']}")
                            
                            # Formats pour acte
                            st.markdown("**Formats pour acte juridique:**")
                            
                            st.markdown("*Format détaillé:*")
                            st.code(societe.format_for_acte())
                            
                            st.markdown("*Format en ligne:*")
                            st.code(societe.format_for_legal_document())
                            
                            if st.button(f"📋 Copier", key=f"copy_{i}"):
                                st.session_state.selected_societe = societe
                                st.success("✅ Informations copiées")
                else:
                    st.warning("Aucun résultat trouvé")

# ===== FONCTIONS D'INTÉGRATION =====

async def enrichir_parties_acte(parties: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
    """
    Enrichit toutes les parties d'un acte juridique
    
    Args:
        parties: Dict avec 'demandeurs' et 'defendeurs'
    
    Returns:
        Dict avec les parties enrichies
    """
    service = CompanyInfoService()
    parties_enrichies = {}
    
    try:
        # Enrichir demandeurs
        if parties.get('demandeurs'):
            parties_enrichies['demandeurs'] = await service.enrichir_parties(
                parties['demandeurs']
            )
        
        # Enrichir défendeurs  
        if parties.get('defendeurs'):
            parties_enrichies['defendeurs'] = await service.enrichir_parties(
                parties['defendeurs']
            )
    finally:
        await service.close()
    
    return parties_enrichies

# Singleton
_company_info_service = None

def get_company_info_service() -> CompanyInfoService:
    """Retourne l'instance singleton du service"""
    global _company_info_service
    if _company_info_service is None:
        _company_info_service = CompanyInfoService()
    return _company_info_service

# Alias pour compatibilité
PappersService = CompanyInfoService
EnrichisseurSocietes = CompanyInfoService