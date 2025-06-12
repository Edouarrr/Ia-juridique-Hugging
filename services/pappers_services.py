"""Service d'enrichissement des informations sociétés via l'API Pappers"""

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import streamlit as st

# Configuration
PAPPERS_API_KEY = os.getenv('PAPPERS_API_KEY')
PAPPERS_BASE_URL = "https://api.pappers.fr/v2"
CACHE_DURATION = timedelta(days=7)  # Cache de 7 jours

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
    
    def __post_init__(self):
        if self.dirigeants is None:
            self.dirigeants = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour l'export"""
        return {
            'nom': self.nom,
            'siren': self.siren,
            'forme_juridique': self.forme_juridique,
            'siege_social': self.siege_social,
            'code_postal': self.code_postal,
            'ville': self.ville,
            'capital_social': self.capital_social,
            'date_creation': self.date_creation,
            'statut': self.statut,
            'dirigeants': self.dirigeants,
            'activite': self.activite,
            'code_naf': self.code_naf,
            'effectif': self.effectif,
            'chiffre_affaires': self.chiffre_affaires,
            'resultat': self.resultat,
            'date_derniers_comptes': self.date_derniers_comptes
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
        
        if self.dirigeants:
            lines.append("Représentée par :")
            for dirigeant in self.dirigeants[:2]:  # Max 2 dirigeants
                lines.append(f"- {dirigeant.get('qualite', '')}: {dirigeant.get('nom', '')}")
        
        return '\n'.join(lines)

# ========================= CACHE LOCAL =========================

class CacheSocietes:
    """Cache local pour éviter les appels API répétés"""
    
    def __init__(self):
        self.cache_file = "cache_societes.json"
        self.cache = self._load_cache()
    
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
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde cache: {e}")
    
    def get(self, key: str) -> Optional[Dict]:
        """Récupère une entrée du cache si elle est valide"""
        if key in self.cache:
            entry = self.cache[key]
            # Vérifier la date d'expiration
            if 'timestamp' in entry:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                if datetime.now() - timestamp < CACHE_DURATION:
                    return entry.get('data')
        return None
    
    def set(self, key: str, data: Dict):
        """Ajoute une entrée au cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()

# ========================= SERVICE PAPPERS =========================

class PappersService:
    """Service principal pour interagir avec l'API Pappers"""
    
    def __init__(self):
        self.api_key = PAPPERS_API_KEY
        self.cache = CacheSocietes()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Assistant-Juridique/1.0'
        })
    
    def search_entreprise(self, query: str) -> List[InfosSociete]:
        """Recherche une entreprise par nom ou SIREN"""
        
        # Vérifier le cache d'abord
        cache_key = f"search_{query.lower()}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return [self._parse_entreprise(e) for e in cached_result]
        
        if not self.api_key:
            return self._fallback_search(query)
        
        try:
            # Appel API
            params = {
                'api_token': self.api_key,
                'q': query,
                'page': 1,
                'par_page': 5
            }
            
            response = self.session.get(
                f"{PAPPERS_BASE_URL}/entreprise/recherche",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                resultats = data.get('resultats', [])
                
                # Mettre en cache
                self.cache.set(cache_key, resultats)
                
                # Parser les résultats
                return [self._parse_entreprise(e) for e in resultats]
            else:
                print(f"Erreur API Pappers: {response.status_code}")
                return self._fallback_search(query)
                
        except Exception as e:
            print(f"Erreur recherche Pappers: {e}")
            return self._fallback_search(query)
    
    def get_entreprise_by_siren(self, siren: str) -> Optional[InfosSociete]:
        """Récupère les informations détaillées d'une entreprise par SIREN"""
        
        # Nettoyer le SIREN
        siren = siren.replace(' ', '').replace('.', '')
        
        # Vérifier le cache
        cache_key = f"siren_{siren}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return self._parse_entreprise(cached_result)
        
        if not self.api_key:
            return None
        
        try:
            params = {
                'api_token': self.api_key,
                'siren': siren
            }
            
            response = self.session.get(
                f"{PAPPERS_BASE_URL}/entreprise",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Mettre en cache
                self.cache.set(cache_key, data)
                
                return self._parse_entreprise(data)
            else:
                print(f"Erreur API Pappers SIREN: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erreur récupération SIREN: {e}")
            return None
    
    def _parse_entreprise(self, data: Dict) -> InfosSociete:
        """Parse les données Pappers en InfosSociete"""
        
        # Informations de base
        nom = data.get('denomination', data.get('nom_entreprise', 'Non renseigné'))
        siren = data.get('siren', '')
        forme_juridique = data.get('forme_juridique', '')
        
        # Siège social
        siege = data.get('siege', {})
        adresse = siege.get('adresse_ligne_1', '')
        code_postal = siege.get('code_postal', '')
        ville = siege.get('ville', '')
        
        # Capital et dates
        capital = data.get('capital', {})
        capital_social = None
        if capital and isinstance(capital, dict):
            capital_social = capital.get('montant')
        
        date_creation = data.get('date_creation')
        
        # Dirigeants
        dirigeants = []
        representants = data.get('representants', [])
        for rep in representants[:3]:  # Max 3 dirigeants
            dirigeant = {
                'nom': f"{rep.get('prenom', '')} {rep.get('nom', '')}".strip(),
                'qualite': rep.get('qualite', '')
            }
            dirigeants.append(dirigeant)
        
        # Activité
        activite = data.get('libelle_code_naf', '')
        code_naf = data.get('code_naf', '')
        
        # Effectif
        effectif = data.get('tranche_effectif', '')
        
        # Financier (si disponible)
        finances = data.get('finances', [])
        chiffre_affaires = None
        resultat = None
        date_derniers_comptes = None
        
        if finances and isinstance(finances, list) and len(finances) > 0:
            dernier_exercice = finances[0]
            chiffre_affaires = dernier_exercice.get('chiffre_affaires')
            resultat = dernier_exercice.get('resultat')
            date_derniers_comptes = dernier_exercice.get('date_cloture')
        
        return InfosSociete(
            nom=nom,
            siren=siren,
            forme_juridique=forme_juridique,
            siege_social=adresse,
            code_postal=code_postal,
            ville=ville,
            capital_social=capital_social,
            date_creation=date_creation,
            dirigeants=dirigeants,
            activite=activite,
            code_naf=code_naf,
            effectif=effectif,
            chiffre_affaires=chiffre_affaires,
            resultat=resultat,
            date_derniers_comptes=date_derniers_comptes
        )
    
    def _fallback_search(self, query: str) -> List[InfosSociete]:
        """Recherche de secours sans API"""
        # Retourner une structure minimale
        return [InfosSociete(
            nom=query,
            siren="[À VÉRIFIER]",
            forme_juridique="[À VÉRIFIER]",
            siege_social="[À VÉRIFIER]",
            code_postal="[À VÉRIFIER]",
            ville="[À VÉRIFIER]"
        )]

# ========================= ENRICHISSEMENT AUTOMATIQUE =========================

class EnrichisseurSocietes:
    """Classe pour enrichir automatiquement les parties dans les actes"""
    
    def __init__(self):
        self.pappers = PappersService()
    
    async def enrichir_parties(self, parties: List[str]) -> List[Dict[str, Any]]:
        """Enrichit une liste de parties avec les informations Pappers"""
        
        parties_enrichies = []
        
        for partie in parties:
            if not partie or len(partie) < 3:
                continue
            
            # Nettoyer le nom
            partie_clean = self._nettoyer_nom_partie(partie)
            
            # Rechercher sur Pappers
            resultats = self.pappers.search_entreprise(partie_clean)
            
            if resultats:
                # Prendre le premier résultat (le plus pertinent)
                societe = resultats[0]
                
                parties_enrichies.append({
                    'nom_original': partie,
                    'nom_societe': societe.nom,
                    'siren': societe.siren,
                    'forme_juridique': societe.forme_juridique,
                    'siege_social': societe.siege_social,
                    'code_postal': societe.code_postal,
                    'ville': societe.ville,
                    'capital_social': societe.capital_social,
                    'dirigeants': societe.dirigeants,
                    'activite': societe.activite,
                    'infos_completes': societe.to_dict()
                })
            else:
                # Pas trouvé - garder le nom original
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
        
        # Enlever les formes juridiques courantes à la fin
        formes = ['SAS', 'SARL', 'SA', 'SCI', 'EURL', 'SASU', 'SNC']
        for forme in formes:
            if nom.upper().endswith(' ' + forme):
                nom = nom[:-len(forme)-1]
        
        return nom.strip()

# ========================= INTERFACE STREAMLIT =========================

def show_enrichissement_interface():
    """Interface Streamlit pour l'enrichissement des sociétés"""
    
    st.header("🏢 Enrichissement des informations sociétés")
    
    if not PAPPERS_API_KEY:
        st.warning("""
        ⚠️ API Pappers non configurée
        
        Pour activer l'enrichissement automatique :
        1. Obtenez une clé API sur [pappers.fr](https://www.pappers.fr/api)
        2. Ajoutez la variable d'environnement : `PAPPERS_API_KEY=votre_cle`
        """)
        st.info("En mode dégradé, les informations devront être complétées manuellement.")
    else:
        st.success("✅ API Pappers configurée")
    
    # Zone de test
    st.subheader("🔍 Tester la recherche")
    
    query = st.text_input(
        "Nom ou SIREN de la société",
        placeholder="Ex: Vinci, 552037806",
        key="test_pappers_query"
    )
    
    if st.button("Rechercher", key="test_pappers_search"):
        if query:
            with st.spinner("Recherche en cours..."):
                service = PappersService()
                resultats = service.search_entreprise(query)
                
                if resultats:
                    st.success(f"✅ {len(resultats)} résultat(s) trouvé(s)")
                    
                    for i, societe in enumerate(resultats, 1):
                        with st.expander(f"{i}. {societe.nom} - {societe.siren}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Informations générales**")
                                st.write(f"• Forme juridique: {societe.forme_juridique}")
                                st.write(f"• Siège: {societe.siege_social}")
                                st.write(f"• {societe.code_postal} {societe.ville}")
                                if societe.capital_social:
                                    st.write(f"• Capital: {societe.capital_social:,} €".replace(',', ' '))
                            
                            with col2:
                                st.write("**Activité**")
                                if societe.activite:
                                    st.write(f"• {societe.activite}")
                                if societe.effectif:
                                    st.write(f"• Effectif: {societe.effectif}")
                                if societe.dirigeants:
                                    st.write("**Dirigeants:**")
                                    for d in societe.dirigeants:
                                        st.write(f"• {d['qualite']}: {d['nom']}")
                            
                            # Format pour acte
                            st.markdown("**Format pour acte juridique:**")
                            st.code(societe.format_for_acte())
                            
                            if st.button(f"Utiliser ces informations", key=f"use_societe_{i}"):
                                st.session_state.selected_societe = societe
                                st.success("✅ Société sélectionnée")
                else:
                    st.warning("Aucun résultat trouvé")

# ========================= FONCTION D'INTÉGRATION =========================

async def enrichir_parties_acte(parties: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
    """
    Enrichit toutes les parties d'un acte juridique
    
    Args:
        parties: Dict avec 'demandeurs' et 'defendeurs'
    
    Returns:
        Dict avec les parties enrichies
    """
    
    enrichisseur = EnrichisseurSocietes()
    parties_enrichies = {}
    
    # Enrichir les demandeurs
    if parties.get('demandeurs'):
        parties_enrichies['demandeurs'] = await enrichisseur.enrichir_parties(
            parties['demandeurs']
        )
    
    # Enrichir les défendeurs
    if parties.get('defendeurs'):
        parties_enrichies['defendeurs'] = await enrichisseur.enrichir_parties(
            parties['defendeurs']
        )
    
    return parties_enrichies

if __name__ == "__main__":
    # Test du service
    print("Service Pappers configuré:", "✅" if PAPPERS_API_KEY else "❌")
    
    if PAPPERS_API_KEY:
        service = PappersService()
        resultats = service.search_entreprise("Vinci")
        
        if resultats:
            print(f"\nTrouvé {len(resultats)} résultats pour 'Vinci':")
            for societe in resultats[:3]:
                print(f"\n{societe.format_for_acte()}")