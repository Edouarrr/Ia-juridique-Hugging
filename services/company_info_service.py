# services/company_info_service.py
"""Service de récupération des informations d'entreprises depuis Pappers et Societe.com"""

import asyncio
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import streamlit as st
from models.dataclasses import InformationEntreprise, SourceEntreprise

class CompanyInfoService:
    """Service pour récupérer les informations légales des entreprises"""
    
    def __init__(self):
        self.pappers_api_key = st.secrets.get("PAPPERS_API_KEY", "")
        self.cache = {}  # Cache simple en mémoire
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def get_company_info(self, company_name: str, 
                             source_preference: SourceEntreprise = SourceEntreprise.PAPPERS) -> Optional[InformationEntreprise]:
        """
        Récupère les informations d'une entreprise
        
        Args:
            company_name: Nom de l'entreprise
            source_preference: Source préférée (Pappers ou Societe.com)
            
        Returns:
            InformationEntreprise ou None si non trouvé
        """
        # Vérifier le cache
        cache_key = f"{company_name.lower()}_{source_preference.value}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Cache valide pendant 24h
            if (datetime.now() - cached['timestamp']).days < 1:
                return cached['data']
        
        # Essayer la source préférée d'abord
        info = None
        if source_preference == SourceEntreprise.PAPPERS and self.pappers_api_key:
            info = await self._fetch_from_pappers(company_name)
        elif source_preference == SourceEntreprise.SOCIETE_COM:
            info = await self._fetch_from_societe_com(company_name)
        
        # Si échec, essayer l'autre source
        if not info:
            if source_preference == SourceEntreprise.PAPPERS:
                info = await self._fetch_from_societe_com(company_name)
            else:
                info = await self._fetch_from_pappers(company_name)
        
        # Mettre en cache si trouvé
        if info:
            self.cache[cache_key] = {
                'data': info,
                'timestamp': datetime.now()
            }
        
        return info
    
    async def _fetch_from_pappers(self, company_name: str) -> Optional[InformationEntreprise]:
        """Récupère depuis l'API Pappers"""
        if not self.pappers_api_key:
            return None
        
        try:
            # Recherche de l'entreprise
            search_url = "https://api.pappers.fr/v2/recherche"
            search_params = {
                "q": company_name,
                "api_token": self.pappers_api_key,
                "par_page": 5
            }
            
            response = await self.session.get(search_url, params=search_params)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get("resultats"):
                return None
            
            # Prendre le premier résultat
            company = data["resultats"][0]
            
            # Récupérer les détails complets si nécessaire
            if company.get("siren"):
                detail_url = f"https://api.pappers.fr/v2/entreprise"
                detail_params = {
                    "siren": company["siren"],
                    "api_token": self.pappers_api_key
                }
                detail_response = await self.session.get(detail_url, params=detail_params)
                if detail_response.status_code == 200:
                    company = detail_response.json()
            
            # Créer l'objet InformationEntreprise
            info = InformationEntreprise(
                siren=company.get("siren"),
                siret=company.get("siege", {}).get("siret"),
                denomination=company.get("nom_entreprise") or company.get("denomination"),
                forme_juridique=company.get("forme_juridique"),
                capital_social=self._parse_capital(company.get("capital")),
                date_creation=self._parse_date(company.get("date_creation")),
                siege_social=self._format_address(company.get("siege", {})),
                code_postal=company.get("siege", {}).get("code_postal"),
                ville=company.get("siege", {}).get("ville"),
                rcs_numero=company.get("numero_rcs"),
                rcs_ville=company.get("greffe"),
                code_ape=company.get("code_naf"),
                activite_principale=company.get("libelle_code_naf"),
                effectif=company.get("tranche_effectif"),
                source=SourceEntreprise.PAPPERS,
                date_recuperation=datetime.now()
            )
            
            # Ajouter les dirigeants
            if company.get("representants"):
                for rep in company["representants"]:
                    info.representants_legaux.append({
                        "nom": rep.get("nom_complet"),
                        "qualite": rep.get("qualite"),
                        "date_prise_poste": rep.get("date_prise_poste")
                    })
            
            return info
            
        except Exception as e:
            print(f"Erreur Pappers: {e}")
            return None
    
    async def _fetch_from_societe_com(self, company_name: str) -> Optional[InformationEntreprise]:
        """Récupère depuis Societe.com par scraping"""
        try:
            # Recherche sur societe.com
            search_url = f"https://www.societe.com/cgi-bin/search"
            search_params = {"champs": company_name}
            
            response = await self.session.get(search_url, params=search_params, follow_redirects=True)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver le premier résultat
            result_link = soup.select_one("div.result a")
            if not result_link:
                return None
            
            # Accéder à la page de l'entreprise
            company_url = f"https://www.societe.com{result_link['href']}"
            company_response = await self.session.get(company_url)
            if company_response.status_code != 200:
                return None
            
            company_soup = BeautifulSoup(company_response.text, 'html.parser')
            
            # Extraire les informations
            info = InformationEntreprise(source=SourceEntreprise.SOCIETE_COM)
            
            # Dénomination
            title = company_soup.select_one("h1")
            if title:
                info.denomination = title.text.strip()
            
            # Table d'identité
            identity_table = company_soup.select_one("table#identite")
            if identity_table:
                rows = identity_table.select("tr")
                for row in rows:
                    cells = row.select("td")
                    if len(cells) >= 2:
                        label = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        if "siren" in label:
                            info.siren = value.replace(" ", "")
                        elif "siret" in label:
                            info.siret = value.replace(" ", "")
                        elif "forme juridique" in label:
                            info.forme_juridique = value
                        elif "capital social" in label:
                            info.capital_social = self._parse_capital(value)
                        elif "adresse" in label:
                            info.siege_social = value
                        elif "ville" in label:
                            info.ville = value
                        elif "code postal" in label:
                            info.code_postal = value
                        elif "rcs" in label:
                            parts = value.split()
                            if len(parts) >= 2:
                                info.rcs_ville = parts[0]
                                info.rcs_numero = " ".join(parts[1:])
                        elif "ape" in label or "naf" in label:
                            info.code_ape = value
                        elif "création" in label:
                            info.date_creation = self._parse_date(value)
                        elif "effectif" in label:
                            info.effectif = value
            
            # Dirigeants
            dirigeants_section = company_soup.select("div#dirigeants")
            if dirigeants_section:
                for dirigeant in dirigeants_section[0].select("div.dirigeant"):
                    nom = dirigeant.select_one("a")
                    qualite = dirigeant.select_one("span.qualite")
                    if nom:
                        info.representants_legaux.append({
                            "nom": nom.text.strip(),
                            "qualite": qualite.text.strip() if qualite else ""
                        })
            
            return info if info.denomination else None
            
        except Exception as e:
            print(f"Erreur Societe.com: {e}")
            return None
    
    def _parse_capital(self, capital_str: str) -> Optional[float]:
        """Parse un montant de capital social"""
        if not capital_str:
            return None
        
        # Retirer les espaces et remplacer les virgules
        capital_str = capital_str.replace(" ", "").replace(",", ".")
        
        # Extraire les chiffres
        match = re.search(r'(\d+(?:\.\d+)?)', capital_str)
        if match:
            return float(match.group(1))
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une date depuis différents formats"""
        if not date_str:
            return None
        
        # Formats courants
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        return None
    
    def _format_address(self, address_data: Dict[str, Any]) -> str:
        """Formate une adresse depuis les données Pappers"""
        parts = []
        
        if address_data.get("numero_voie"):
            parts.append(address_data["numero_voie"])
        if address_data.get("type_voie"):
            parts.append(address_data["type_voie"])
        if address_data.get("libelle_voie"):
            parts.append(address_data["libelle_voie"])
        
        address = " ".join(parts)
        
        # Ajouter code postal et ville
        if address_data.get("code_postal") and address_data.get("ville"):
            address += f", {address_data['code_postal']} {address_data['ville']}"
        
        return address
    
    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche multiple d'entreprises"""
        results = []
        
        if self.pappers_api_key:
            try:
                search_url = "https://api.pappers.fr/v2/recherche"
                params = {
                    "q": query,
                    "api_token": self.pappers_api_key,
                    "par_page": limit
                }
                
                response = await self.session.get(search_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for company in data.get("resultats", []):
                        results.append({
                            "nom": company.get("nom_entreprise"),
                            "siren": company.get("siren"),
                            "forme_juridique": company.get("forme_juridique"),
                            "ville": company.get("siege", {}).get("ville"),
                            "source": "Pappers"
                        })
            except:
                pass
        
        return results
    
    def format_for_legal_document(self, info: InformationEntreprise) -> str:
        """Formate les informations pour un document juridique"""
        parts = [info.denomination]
        
        if info.forme_juridique:
            parts.append(f", {info.forme_juridique}")
        
        if info.capital_social:
            parts.append(f" au capital de {info.format_capital()}")
        
        if info.get_immatriculation_complete():
            parts.append(f", immatriculée au {info.get_immatriculation_complete()}")
        
        if info.siege_social:
            parts.append(f", dont le siège social est situé {info.siege_social}")
        
        if info.representants_legaux:
            rep = info.representants_legaux[0]
            parts.append(f", représentée par {rep['nom']}")
            if rep.get('qualite'):
                parts.append(f" en sa qualité de {rep['qualite']}")
        
        return "".join(parts)
    
    async def close(self):
        """Ferme la session HTTP"""
        await self.session.aclose()

# Singleton pour éviter les connexions multiples
_company_info_service = None

def get_company_info_service() -> CompanyInfoService:
    """Retourne l'instance singleton du service"""
    global _company_info_service
    if _company_info_service is None:
        _company_info_service = CompanyInfoService()
    return _company_info_service