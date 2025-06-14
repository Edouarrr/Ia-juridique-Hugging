# managers/company_info_manager.py
"""Gestionnaire des informations d'entreprises depuis Pappers et Societe.com"""

import asyncio
import json
import logging
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("Module httpx non disponible")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("Module beautifulsoup4 non disponible")

import streamlit as st

from models.dataclasses import (InformationEntreprise, Partie, PhaseProcedure,
                                SourceEntreprise, StatutProcedural, TypePartie,
                                create_partie_from_name_with_lookup)


class CompanyInfoManager:
    """Gestionnaire pour récupérer les informations légales des entreprises"""
    
    def __init__(self):
        self.pappers_api_key = st.secrets.get("PAPPERS_API_KEY", "")
        self.cache = {}  # Cache en mémoire
        self.cache_duration = timedelta(days=7)  # Cache valide 7 jours
        
        # Session HTTP
        if HTTPX_AVAILABLE:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        else:
            self.session = None
            logger.error("httpx non disponible - fonctionnalités limitées")
    
    async def __aenter__(self):
        """Contexte manager pour usage async"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermeture propre"""
        if self.session:
            await self.session.aclose()
    
    async def get_company_info(self, company_name: str, 
                             source_preference: SourceEntreprise = SourceEntreprise.PAPPERS,
                             force_refresh: bool = False) -> Optional[InformationEntreprise]:
        """
        Récupère les informations d'une entreprise
        
        Args:
            company_name: Nom de l'entreprise
            source_preference: Source préférée (Pappers ou Societe.com)
            force_refresh: Forcer le rafraîchissement du cache
            
        Returns:
            InformationEntreprise ou None si non trouvé
        """
        if not HTTPX_AVAILABLE:
            logger.error("httpx requis pour la récupération d'informations")
            return None
        
        # Vérifier le cache
        cache_key = f"{company_name.lower()}_{source_preference.value}"
        if not force_refresh and cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached['timestamp'] < self.cache_duration:
                logger.info(f"Utilisation du cache pour {company_name}")
                return cached['data']
        
        # Essayer la source préférée d'abord
        info = None
        try:
            if source_preference == SourceEntreprise.PAPPERS and self.pappers_api_key:
                info = await self._fetch_from_pappers(company_name)
            elif source_preference == SourceEntreprise.SOCIETE_COM and BS4_AVAILABLE:
                info = await self._fetch_from_societe_com(company_name)
            
            # Si échec, essayer l'autre source
            if not info:
                if source_preference == SourceEntreprise.PAPPERS and BS4_AVAILABLE:
                    logger.info(f"Pappers échoué, essai sur Societe.com pour {company_name}")
                    info = await self._fetch_from_societe_com(company_name)
                elif source_preference == SourceEntreprise.SOCIETE_COM and self.pappers_api_key:
                    logger.info(f"Societe.com échoué, essai sur Pappers pour {company_name}")
                    info = await self._fetch_from_pappers(company_name)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération pour {company_name}: {e}")
        
        # Mettre en cache si trouvé
        if info:
            self.cache[cache_key] = {
                'data': info,
                'timestamp': datetime.now()
            }
            logger.info(f"Informations trouvées et mises en cache pour {company_name}")
        
        return info
    
    async def _fetch_from_pappers(self, company_name: str) -> Optional[InformationEntreprise]:
        """Récupère depuis l'API Pappers"""
        if not self.pappers_api_key:
            logger.warning("Clé API Pappers non configurée")
            return None
        
        try:
            # Recherche de l'entreprise
            search_url = "https://api.pappers.fr/v2/recherche"
            search_params = {
                "q": company_name,
                "api_token": self.pappers_api_key,
                "par_page": 5,
                "entreprise_cessee": False  # Exclure les entreprises fermées
            }
            
            logger.info(f"Recherche Pappers pour: {company_name}")
            response = await self.session.get(search_url, params=search_params)
            
            if response.status_code == 401:
                logger.error("Clé API Pappers invalide")
                return None
            elif response.status_code != 200:
                logger.error(f"Erreur Pappers: {response.status_code}")
                return None
            
            data = response.json()
            if not data.get("resultats"):
                logger.info(f"Aucun résultat Pappers pour {company_name}")
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
                
                logger.info(f"Récupération détails pour SIREN: {company['siren']}")
                detail_response = await self.session.get(detail_url, params=detail_params)
                
                if detail_response.status_code == 200:
                    company = detail_response.json()
            
            # Créer l'objet InformationEntreprise
            info = InformationEntreprise(
                siren=company.get("siren"),
                siret=company.get("siege", {}).get("siret") or company.get("siret"),
                denomination=self._clean_company_name(
                    company.get("nom_entreprise") or 
                    company.get("denomination") or
                    company.get("nom_complet")
                ),
                forme_juridique=company.get("forme_juridique"),
                capital_social=self._parse_capital(company.get("capital")),
                devise_capital=company.get("devise_capital", "EUR"),
                date_creation=self._parse_date(company.get("date_creation")),
                date_cloture_exercice=company.get("date_cloture_exercice"),
                siege_social=self._format_address_pappers(company.get("siege", {})),
                code_postal=company.get("siege", {}).get("code_postal"),
                ville=company.get("siege", {}).get("ville"),
                rcs_numero=self._extract_rcs_number(company.get("numero_rcs")),
                rcs_ville=company.get("greffe"),
                code_ape=company.get("code_naf"),
                activite_principale=company.get("libelle_code_naf"),
                effectif=company.get("tranche_effectif"),
                chiffre_affaires=self._parse_number(company.get("chiffre_affaires")),
                source=SourceEntreprise.PAPPERS,
                date_recuperation=datetime.now(),
                derniere_mise_a_jour=self._parse_date(company.get("date_mise_a_jour")),
                fiable=True
            )
            
            # Ajouter le numéro TVA intracommunautaire
            if company.get("siren"):
                info.tva_intracommunautaire = self._generate_tva_number(company["siren"])
            
            # Ajouter les dirigeants
            if company.get("representants"):
                for rep in company["representants"]:
                    if rep.get("actif", True):  # Seulement les dirigeants actifs
                        info.representants_legaux.append({
                            "nom": rep.get("nom_complet", ""),
                            "qualite": rep.get("qualite", ""),
                            "date_prise_poste": rep.get("date_prise_poste", ""),
                            "adresse": rep.get("adresse_ligne_1", "")
                        })
            
            return info
            
        except Exception as e:
            logger.error(f"Erreur Pappers pour {company_name}: {e}", exc_info=True)
            return None
    
    async def _fetch_from_societe_com(self, company_name: str) -> Optional[InformationEntreprise]:
        """Récupère depuis Societe.com par scraping"""
        if not BS4_AVAILABLE:
            logger.error("BeautifulSoup4 requis pour Societe.com")
            return None
        
        try:
            # Recherche sur societe.com
            search_url = f"https://www.societe.com/cgi-bin/search"
            search_params = {"champs": company_name}
            
            logger.info(f"Recherche Societe.com pour: {company_name}")
            response = await self.session.get(
                search_url, 
                params=search_params, 
                follow_redirects=True
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur HTTP Societe.com: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Vérifier si redirection directe vers une fiche
            if '/societe/' in str(response.url):
                company_url = str(response.url)
            else:
                # Sinon, chercher le premier résultat
                result_link = soup.select_one("div.result a.txt")
                if not result_link:
                    logger.info(f"Aucun résultat Societe.com pour {company_name}")
                    return None
                
                company_url = f"https://www.societe.com{result_link['href']}"
            
            # Accéder à la page de l'entreprise
            logger.info(f"Accès à la fiche: {company_url}")
            company_response = await self.session.get(company_url)
            
            if company_response.status_code != 200:
                logger.error(f"Erreur accès fiche: {company_response.status_code}")
                return None
            
            company_soup = BeautifulSoup(company_response.text, 'html.parser')
            
            # Extraire les informations
            info = InformationEntreprise(source=SourceEntreprise.SOCIETE_COM)
            
            # Dénomination
            title_elem = company_soup.select_one("h1") or company_soup.select_one("span.break")
            if title_elem:
                info.denomination = self._clean_company_name(title_elem.text.strip())
            
            # Table d'identité
            identity_section = company_soup.select_one("#identite")
            if identity_section:
                # Parser chaque ligne de la table
                for row in identity_section.select("tr"):
                    cells = row.select("td")
                    if len(cells) >= 2:
                        label = cells[0].text.strip().lower()
                        value = cells[1].text.strip()
                        
                        if not value or value == "-":
                            continue
                        
                        if "siren" in label:
                            info.siren = value.replace(" ", "")
                        elif "siret" in label and "siège" in label:
                            info.siret = value.replace(" ", "")
                        elif "forme juridique" in label:
                            info.forme_juridique = value
                        elif "capital social" in label or "capital" in label:
                            info.capital_social = self._parse_capital(value)
                        elif "adresse" in label and "siège" in label:
                            info.siege_social = value
                        elif "ville" in label:
                            info.ville = value
                        elif "code postal" in label:
                            info.code_postal = value
                        elif "rcs" in label or "registre" in label:
                            rcs_parts = value.split()
                            if len(rcs_parts) >= 2:
                                info.rcs_ville = rcs_parts[0]
                                info.rcs_numero = " ".join(rcs_parts[1:])
                        elif "ape" in label or "naf" in label:
                            info.code_ape = value.split()[0] if value else None
                        elif "activité" in label:
                            info.activite_principale = value
                        elif "création" in label or "immatriculation" in label:
                            info.date_creation = self._parse_date(value)
                        elif "effectif" in label:
                            info.effectif = value
                        elif "chiffre" in label and "affaires" in label:
                            info.chiffre_affaires = self._parse_number(value)
            
            # Dirigeants
            dirigeants_section = company_soup.select("#dirigeants table tr")
            for row in dirigeants_section:
                nom_elem = row.select_one("a.name")
                qualite_elem = row.select_one("span")
                
                if nom_elem:
                    dirigeant = {
                        "nom": nom_elem.text.strip(),
                        "qualite": qualite_elem.text.strip() if qualite_elem else ""
                    }
                    
                    # Extraire date si présente
                    date_text = row.text
                    date_match = re.search(r'depuis le (\d{2}/\d{2}/\d{4})', date_text)
                    if date_match:
                        dirigeant["date_prise_poste"] = date_match.group(1)
                    
                    info.representants_legaux.append(dirigeant)
            
            # Générer le numéro TVA si SIREN disponible
            if info.siren:
                info.tva_intracommunautaire = self._generate_tva_number(info.siren)
            
            # Vérifier qu'on a au moins les infos minimales
            if not info.denomination or not info.siren:
                logger.warning(f"Informations insuffisantes pour {company_name}")
                return None
            
            return info
            
        except Exception as e:
            logger.error(f"Erreur Societe.com pour {company_name}: {e}", exc_info=True)
            return None
    
    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche multiple d'entreprises"""
        results = []
        
        if self.pappers_api_key and HTTPX_AVAILABLE:
            try:
                search_url = "https://api.pappers.fr/v2/recherche"
                params = {
                    "q": query,
                    "api_token": self.pappers_api_key,
                    "par_page": limit,
                    "entreprise_cessee": False
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
                            "code_postal": company.get("siege", {}).get("code_postal"),
                            "dirigeant": company.get("representants", [{}])[0].get("nom_complet", "") if company.get("representants") else "",
                            "activite": company.get("libelle_code_naf", ""),
                            "source": "Pappers"
                        })
            except Exception as e:
                logger.error(f"Erreur recherche multiple: {e}")
        
        return results
    
    async def enrich_partie(self, partie: Partie, force_refresh: bool = False) -> Partie:
        """Enrichit une partie avec les informations d'entreprise"""
        if partie.type_personne != "morale" or partie.info_entreprise:
            return partie
        
        logger.info(f"Enrichissement de la partie: {partie.nom}")
        
        # Rechercher les informations
        info = await self.get_company_info(partie.nom, force_refresh=force_refresh)
        
        if info:
            partie.update_from_entreprise_info(info)
            logger.info(f"Partie {partie.nom} enrichie avec succès")
        else:
            logger.warning(f"Aucune information trouvée pour {partie.nom}")
        
        return partie
    
    async def enrich_multiple_parties(self, parties: List[Partie], 
                                    progress_callback=None) -> List[Partie]:
        """Enrichit plusieurs parties en parallèle"""
        enriched_parties = []
        
        # Filtrer les parties à enrichir
        parties_to_enrich = [
            p for p in parties 
            if p.type_personne == "morale" and not p.info_entreprise
        ]
        
        if not parties_to_enrich:
            return parties
        
        # Traiter par batch pour éviter trop de requêtes simultanées
        batch_size = 3
        
        for i in range(0, len(parties_to_enrich), batch_size):
            batch = parties_to_enrich[i:i + batch_size]
            
            # Créer les tâches d'enrichissement
            tasks = [self.enrich_partie(partie) for partie in batch]
            
            # Exécuter en parallèle
            enriched_batch = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traiter les résultats
            for j, result in enumerate(enriched_batch):
                if isinstance(result, Exception):
                    logger.error(f"Erreur enrichissement: {result}")
                    enriched_parties.append(batch[j])  # Garder l'original
                else:
                    enriched_parties.append(result)
            
            # Callback de progression
            if progress_callback:
                progress = (i + len(batch)) / len(parties_to_enrich)
                progress_callback(progress)
        
        # Ajouter les parties non enrichies (personnes physiques)
        for partie in parties:
            if partie.type_personne != "morale":
                enriched_parties.append(partie)
        
        return enriched_parties
    
    def format_for_legal_document(self, info: InformationEntreprise, 
                                style: str = "complet") -> str:
        """
        Formate les informations pour un document juridique
        
        Args:
            info: Informations de l'entreprise
            style: Style de formatage ('complet', 'simple', 'assignation')
        """
        if style == "simple":
            # Format simple pour mentions rapides
            parts = [info.denomination]
            if info.forme_juridique:
                parts.append(f"({info.forme_juridique})")
            return " ".join(parts)
        
        elif style == "assignation":
            # Format pour assignation
            parts = [info.denomination]
            
            if info.forme_juridique:
                parts.append(f", société {info.forme_juridique}")
            
            if info.capital_social:
                parts.append(f" au capital de {info.format_capital()}")
            
            if info.get_immatriculation_complete():
                parts.append(f", immatriculée au {info.get_immatriculation_complete()}")
            
            if info.siege_social:
                parts.append(f", dont le siège social est sis {info.siege_social}")
            
            if info.representants_legaux:
                rep = info.representants_legaux[0]
                parts.append(f", prise en la personne de son représentant légal")
            
            return "".join(parts)
        
        else:  # style == "complet"
            # Format complet standard
            parts = [info.denomination]
            
            if info.forme_juridique:
                parts.append(f", {info.forme_juridique}")
            
            if info.capital_social:
                parts.append(f" au capital social de {info.format_capital()}")
            
            if info.get_immatriculation_complete():
                parts.append(f", immatriculée au {info.get_immatriculation_complete()}")
            
            if info.siren:
                parts.append(f", SIREN {info.siren}")
            
            if info.siege_social:
                parts.append(f", dont le siège social est situé {info.siege_social}")
            
            if info.representants_legaux:
                rep = info.representants_legaux[0]
                parts.append(f", représentée par {rep['nom']}")
                if rep.get('qualite'):
                    parts.append(f" en sa qualité de {rep['qualite']}")
            
            return "".join(parts)
    
    def _clean_company_name(self, name: str) -> str:
        """Nettoie le nom d'entreprise"""
        if not name:
            return ""
        
        # Retirer les espaces multiples
        name = re.sub(r'\s+', ' ', name)
        
        # Retirer les parenthèses vides
        name = re.sub(r'\(\s*\)', '', name)
        
        # Capitaliser correctement
        name = name.strip()
        
        return name
    
    def _parse_capital(self, capital_str: str) -> Optional[float]:
        """Parse un montant de capital social"""
        if not capital_str:
            return None
        
        # Retirer tout sauf les chiffres et virgules/points
        capital_str = re.sub(r'[^\d,.]', '', capital_str)
        
        if not capital_str:
            return None
        
        # Remplacer les virgules par des points
        capital_str = capital_str.replace(',', '.')
        
        # Si plusieurs points, garder seulement le dernier comme décimal
        parts = capital_str.split('.')
        if len(parts) > 2:
            capital_str = ''.join(parts[:-1]) + '.' + parts[-1]
        
        try:
            return float(capital_str)
        except ValueError:
            return None
    
    def _parse_number(self, number_str: str) -> Optional[float]:
        """Parse un nombre (CA, effectif, etc.)"""
        if not number_str:
            return None
        
        # Extraire le nombre
        match = re.search(r'([\d\s,\.]+)', number_str)
        if not match:
            return None
        
        number = match.group(1)
        # Retirer les espaces
        number = number.replace(' ', '')
        # Gérer le format français (virgule comme décimal)
        number = number.replace(',', '.')
        
        try:
            value = float(number)
            
            # Gérer les multiplicateurs (K, M)
            if 'K' in number_str.upper():
                value *= 1000
            elif 'M' in number_str.upper():
                value *= 1000000
            
            return value
        except ValueError:
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
            "%d %b %Y",
            "%Y%m%d"
        ]
        
        # Nettoyer la date
        date_str = date_str.strip()
        date_str = re.sub(r'[^\d\-/\s\w]', '', date_str)
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # Essayer avec dateutil si disponible
        try:
            from dateutil.parser import parse
            return parse(date_str, dayfirst=True)
        except:
            pass
        
        return None
    
    def _format_address_pappers(self, address_data: Dict[str, Any]) -> str:
        """Formate une adresse depuis les données Pappers"""
        if not address_data:
            return ""
        
        parts = []
        
        # Numéro et voie
        if address_data.get("numero_voie"):
            parts.append(str(address_data["numero_voie"]))
        
        if address_data.get("indice_repetition"):
            parts.append(address_data["indice_repetition"])
        
        if address_data.get("type_voie"):
            parts.append(address_data["type_voie"])
        
        if address_data.get("libelle_voie"):
            parts.append(address_data["libelle_voie"])
        
        # Complément
        if address_data.get("complement"):
            parts.append(f", {address_data['complement']}")
        
        # Code postal et ville
        if address_data.get("code_postal") and address_data.get("ville"):
            if parts:
                parts.append(f", {address_data['code_postal']} {address_data['ville']}")
            else:
                parts.append(f"{address_data['code_postal']} {address_data['ville']}")
        
        return " ".join(parts)
    
    def _extract_rcs_number(self, rcs_str: str) -> Optional[str]:
        """Extrait le numéro RCS propre"""
        if not rcs_str:
            return None
        
        # Retirer le préfixe RCS si présent
        rcs_str = re.sub(r'^RCS\s+', '', rcs_str, flags=re.IGNORECASE)
        
        # Extraire le numéro (format: 123 456 789)
        match = re.search(r'(\d{3}\s?\d{3}\s?\d{3})', rcs_str)
        if match:
            return match.group(1)
        
        return rcs_str
    
    def _generate_tva_number(self, siren: str) -> str:
        """Génère le numéro de TVA intracommunautaire français"""
        if not siren or len(siren) != 9:
            return ""
        
        # Clé = (12 + 3 * (SIREN % 97)) % 97
        try:
            siren_int = int(siren)
            key = (12 + 3 * (siren_int % 97)) % 97
            return f"FR{key:02d}{siren}"
        except ValueError:
            return ""
    
    def export_to_csv(self, companies: List[InformationEntreprise], 
                     filename: str = "entreprises.csv"):
        """Exporte une liste d'entreprises en CSV"""
        import csv
        import io
        
        output = io.StringIO()
        
        # Définir les colonnes
        fieldnames = [
            'denomination', 'forme_juridique', 'siren', 'siret',
            'capital_social', 'siege_social', 'code_postal', 'ville',
            'rcs_numero', 'rcs_ville', 'code_ape', 'activite_principale',
            'effectif', 'representant_legal', 'source', 'date_recuperation'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for company in companies:
            row = {
                'denomination': company.denomination,
                'forme_juridique': company.forme_juridique or '',
                'siren': company.siren or '',
                'siret': company.siret or '',
                'capital_social': company.capital_social or '',
                'siege_social': company.siege_social or '',
                'code_postal': company.code_postal or '',
                'ville': company.ville or '',
                'rcs_numero': company.rcs_numero or '',
                'rcs_ville': company.rcs_ville or '',
                'code_ape': company.code_ape or '',
                'activite_principale': company.activite_principale or '',
                'effectif': company.effectif or '',
                'representant_legal': company.representants_legaux[0]['nom'] if company.representants_legaux else '',
                'source': company.source.value,
                'date_recuperation': company.date_recuperation.strftime('%d/%m/%Y')
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def save_cache(self, filepath: str = "company_cache.json"):
        """Sauvegarde le cache dans un fichier"""
        cache_data = {}
        
        for key, value in self.cache.items():
            cache_data[key] = {
                'data': asdict(value['data']),
                'timestamp': value['timestamp'].isoformat()
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    def load_cache(self, filepath: str = "company_cache.json"):
        """Charge le cache depuis un fichier"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for key, value in cache_data.items():
                # Recréer l'objet InformationEntreprise
                info_dict = value['data']
                # Convertir les dates
                for date_field in ['date_creation', 'date_recuperation', 'derniere_mise_a_jour']:
                    if info_dict.get(date_field):
                        info_dict[date_field] = datetime.fromisoformat(info_dict[date_field])
                
                # Convertir l'enum
                if info_dict.get('source'):
                    info_dict['source'] = SourceEntreprise(info_dict['source'])
                
                self.cache[key] = {
                    'data': InformationEntreprise(**info_dict),
                    'timestamp': datetime.fromisoformat(value['timestamp'])
                }
            
            logger.info(f"Cache chargé: {len(self.cache)} entreprises")
        except FileNotFoundError:
            logger.info("Aucun fichier de cache trouvé")
        except Exception as e:
            logger.error(f"Erreur chargement cache: {e}")

# Instance singleton
_company_info_manager = None

def get_company_info_manager() -> CompanyInfoManager:
    """Retourne l'instance singleton du gestionnaire"""
    global _company_info_manager
    if _company_info_manager is None:
        _company_info_manager = CompanyInfoManager()
    return _company_info_manager