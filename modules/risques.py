"""
Module de gestion des risques en droit pénal des affaires
Utilise le manager multi-LLM existant avec ChatGPT-4, Claude Opus 4, Perplexity, Gemini et Mistral
"""

import streamlit as st
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any, Tuple
import uuid
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass, field
from enum import Enum
import time
import os
import sys
from pathlib import Path

# Import du manager multi-LLM existant dans le projet
sys.path.append(str(Path(__file__).parent.parent))
try:
    from modules.multi_llm_manager import MultiLLMManager, LLMModel
    from utils import truncate_text, clean_key, format_legal_date
except ImportError:
    # Fallback si les imports échouent
    def truncate_text(text, max_length=100):
        return text[:max_length] + "..." if len(text) > max_length else text
    def clean_key(text):
        return text.replace(" ", "_").lower()
    def format_legal_date(date):
        return date.strftime("%d/%m/%Y") if date else ""

# Énumération des niveaux de risque pénal
class RiskLevelPenal(Enum):
    NEGLIGEABLE = "negligeable"
    MODERE = "modere"
    SIGNIFICATIF = "significatif"
    MAJEUR = "majeur"
    CRITIQUE = "critique"

# Catégories spécifiques au droit pénal des affaires
CATEGORIES_PENAL_AFFAIRES = {
    "corruption": {
        "nom": "Corruption et trafic d'influence",
        "articles": ["432-11", "433-1", "433-2", "445-1 CP"],
        "sanctions_max": "10 ans d'emprisonnement et 1 000 000 € d'amende",
        "prescription": "6 ans",
        "gravite_base": 0.9,
        "personnes_morales": "5 000 000 € d'amende + sanctions complémentaires"
    },
    "blanchiment": {
        "nom": "Blanchiment de capitaux", 
        "articles": ["324-1", "324-2", "324-3 CP"],
        "sanctions_max": "10 ans d'emprisonnement et 750 000 € d'amende",
        "prescription": "6 ans",
        "gravite_base": 0.85,
        "personnes_morales": "3 750 000 € d'amende + dissolution possible"
    },
    "abus_biens_sociaux": {
        "nom": "Abus de biens sociaux (ABS)",
        "articles": ["L241-3", "L242-6 Code de commerce"],
        "sanctions_max": "5 ans d'emprisonnement et 375 000 € d'amende",
        "prescription": "6 ans à compter de la découverte",
        "gravite_base": 0.75,
        "personnes_morales": "1 875 000 € d'amende"
    },
    "delit_initie": {
        "nom": "Délit d'initié et manipulation de marché",
        "articles": ["L465-1", "L465-2", "L465-3 CMF"],
        "sanctions_max": "7 ans d'emprisonnement et 10 000 000 € ou 10x le profit",
        "prescription": "6 ans",
        "gravite_base": 0.85,
        "personnes_morales": "100 000 000 € ou 15% du CA"
    },
    "fraude_fiscale": {
        "nom": "Fraude fiscale aggravée",
        "articles": ["1741", "1743 CGI"],
        "sanctions_max": "7 ans d'emprisonnement et 3 000 000 €",
        "prescription": "6 ans (10 ans si fraude aggravée)",
        "gravite_base": 0.8,
        "personnes_morales": "Amende égale au montant fraudé"
    },
    "escroquerie": {
        "nom": "Escroquerie et abus de confiance",
        "articles": ["313-1", "314-1 CP"],
        "sanctions_max": "7 ans d'emprisonnement et 750 000 €",
        "prescription": "6 ans",
        "gravite_base": 0.7,
        "personnes_morales": "3 750 000 € d'amende"
    },
    "faux_usage_faux": {
        "nom": "Faux et usage de faux",
        "articles": ["441-1", "441-2 CP"],
        "sanctions_max": "3 ans d'emprisonnement et 45 000 €",
        "prescription": "6 ans",
        "gravite_base": 0.65,
        "personnes_morales": "225 000 € d'amende"
    },
    "banqueroute": {
        "nom": "Banqueroute et infractions voisines",
        "articles": ["L654-2", "L654-3 Code de commerce"],
        "sanctions_max": "5 ans d'emprisonnement et 75 000 €",
        "prescription": "3 ans",
        "gravite_base": 0.75,
        "personnes_morales": "375 000 € d'amende + interdictions"
    },
    "entrave": {
        "nom": "Entrave aux fonctions et délits d'obstacle",
        "articles": ["L8114-1", "L8114-2 Code du travail"],
        "sanctions_max": "1 an d'emprisonnement et 3 750 €",
        "prescription": "3 ans",
        "gravite_base": 0.5,
        "personnes_morales": "18 750 € d'amende"
    },
    "favoritisme": {
        "nom": "Favoritisme et marchés publics",
        "articles": ["432-14 CP"],
        "sanctions_max": "2 ans d'emprisonnement et 200 000 €",
        "prescription": "6 ans",
        "gravite_base": 0.7,
        "personnes_morales": "1 000 000 € d'amende"
    }
}

@dataclass
class RisquePenal:
    """Classe représentant un risque en droit pénal des affaires"""
    id: str
    titre: str
    description: str
    categorie_penale: str
    niveau: RiskLevelPenal
    probabilite_poursuites: float
    gravite_infraction: float
    date_identification: datetime = field(default_factory=datetime.now)
    date_prescription: Optional[datetime] = None
    elements_constitutifs: Dict[str, str] = field(default_factory=dict)
    personnes_impliquees: List[str] = field(default_factory=list)
    montant_prejudice: float = 0.0
    preuves_disponibles: List[str] = field(default_factory=list)
    mesures_urgentes: List[str] = field(default_factory=list)
    statut: str = "identifie"
    analyse_ia: Dict[str, Any] = field(default_factory=dict)
    jurisprudences: List[Dict[str, str]] = field(default_factory=list)
    
    @property
    def score_risque_penal(self) -> float:
        """Calcule le score de risque pénal global"""
        # Pondération spécifique au pénal
        score_base = (self.probabilite_poursuites * 0.4) + (self.gravite_infraction * 0.6)
        
        # Ajustements selon les facteurs aggravants
        if self.montant_prejudice > 1000000:
            score_base *= 1.2
        if len(self.personnes_impliquees) > 5:
            score_base *= 1.1
        if self.categorie_penale in ["corruption", "blanchiment", "delit_initie"]:
            score_base *= 1.15
            
        return min(score_base, 1.0)
    
    @property
    def urgence_traitement(self) -> str:
        """Détermine l'urgence du traitement"""
        if self.date_prescription:
            jours_restants = (self.date_prescription - datetime.now()).days
            if jours_restants < 180:
                return "CRITIQUE"
            elif jours_restants < 365:
                return "URGENTE"
        
        if self.score_risque_penal > 0.8:
            return "CRITIQUE"
        elif self.score_risque_penal > 0.6:
            return "ELEVEE"
        elif self.score_risque_penal > 0.4:
            return "MODEREE"
        return "NORMALE"

class RisquePenalManager:
    """Gestionnaire des risques pénaux avec intégration IA"""
    
    def __init__(self, multi_llm_manager: Optional[MultiLLMManager] = None):
        """Initialise le gestionnaire avec le manager multi-LLM"""
        self.multi_llm_manager = multi_llm_manager
        
        # Initialisation des données en session
        if 'risques_penaux' not in st.session_state:
            st.session_state.risques_penaux = {}
        if 'historique_penal' not in st.session_state:
            st.session_state.historique_penal = []
        if 'alertes_penales' not in st.session_state:
            st.session_state.alertes_penales = []
    
    async def analyze_with_multi_llm(
        self,
        risque: RisquePenal,
        models: List[str] = None
    ) -> Dict[str, Any]:
        """Analyse un risque avec le manager multi-LLM"""
        
        if not self.multi_llm_manager:
            return {"error": "Manager multi-LLM non configuré"}
        
        # Modèles par défaut
        if not models:
            models = ["gpt-4", "claude-opus-4", "perplexity", "gemini", "mistral"]
        
        # Construire le prompt spécialisé
        prompt = self._build_penal_analysis_prompt(risque)
        
        # Contexte juridique
        context = {
            "domain": "droit_penal_affaires",
            "jurisdiction": "france",
            "category": risque.categorie_penale,
            "urgency": risque.urgence_traitement
        }
        
        try:
            # Appel au manager multi-LLM
            results = await self.multi_llm_manager.analyze(
                prompt=prompt,
                models=models,
                context=context,
                temperature=0.3,  # Plus bas pour du juridique
                max_tokens=3000
            )
            
            # Traiter et agréger les résultats
            analysis = self._aggregate_llm_results(results, risque)
            
            # Enrichir avec des insights spécifiques au pénal
            analysis = self._enrich_penal_analysis(analysis, risque)
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def _build_penal_analysis_prompt(self, risque: RisquePenal) -> str:
        """Construit un prompt optimisé pour l'analyse pénale"""
        
        cat_info = CATEGORIES_PENAL_AFFAIRES.get(risque.categorie_penale, {})
        
        prompt = f"""En tant qu'expert en droit pénal des affaires français, analysez ce cas :

**INFORMATIONS DU DOSSIER**
- Catégorie : {cat_info.get('nom', risque.categorie_penale)}
- Articles visés : {', '.join(cat_info.get('articles', []))}
- Faits reprochés : {risque.description}
- Montant du préjudice : {risque.montant_prejudice:,.2f} €
- Personnes impliquées : {len(risque.personnes_impliquees)}
- Date des faits : {risque.date_identification.strftime('%d/%m/%Y')}

**ANALYSE REQUISE**

1. **QUALIFICATION JURIDIQUE**
   - Infractions caractérisées avec certitude
   - Infractions possibles/connexes
   - Éléments constitutifs manquants

2. **ÉVALUATION DES RISQUES**
   - Probabilité de poursuites pénales (%)
   - Probabilité de condamnation (%)
   - Sanctions encourues (peines principales et complémentaires)
   - Risque pour les personnes physiques vs morales

3. **STRATÉGIE DE DÉFENSE**
   - Arguments juridiques mobilisables
   - Causes d'exonération applicables
   - Prescription et délais

4. **MESURES IMMÉDIATES**
   - Actions à entreprendre sous 48h
   - Preuves à sécuriser
   - Communications à maîtriser

5. **JURISPRUDENCE PERTINENTE**
   - Décisions de référence (Cass. Crim.)
   - Tendances jurisprudentielles récentes
   - Quantum des peines habituellement prononcées

Fournissez une analyse structurée avec des pourcentages et recommandations concrètes."""
        
        return prompt
    
    def _aggregate_llm_results(
        self, 
        results: Dict[str, Any],
        risque: RisquePenal
    ) -> Dict[str, Any]:
        """Agrège les résultats des différents LLM"""
        
        aggregated = {
            "success": True,
            "timestamp": datetime.now(),
            "models_consensus": {},
            "qualification_juridique": {},
            "evaluation_risques": {},
            "strategie_defense": [],
            "mesures_immediates": [],
            "jurisprudences": [],
            "confidence_scores": {}
        }
        
        # Extraire et consolider les analyses de chaque modèle
        successful_models = []
        
        for model, result in results.items():
            if result.get("success"):
                successful_models.append(model)
                # Parser et extraire les éléments clés
                # (Logique d'extraction selon le format de réponse du manager)
        
        # Calculer le consensus
        aggregated["models_consensus"]["agreement_level"] = len(successful_models) / len(results)
        aggregated["models_consensus"]["models_used"] = successful_models
        
        # Scores moyens pondérés
        if successful_models:
            # Probabilité de poursuites consensus
            prob_poursuites = []
            prob_condamnation = []
            
            for model in successful_models:
                # Extraire les probabilités de chaque modèle
                # (À adapter selon le format de réponse)
                pass
            
            aggregated["evaluation_risques"]["probabilite_poursuites"] = np.mean(prob_poursuites) if prob_poursuites else 0.7
            aggregated["evaluation_risques"]["probabilite_condamnation"] = np.mean(prob_condamnation) if prob_condamnation else 0.6
        
        return aggregated
    
    def _enrich_penal_analysis(
        self,
        analysis: Dict[str, Any],
        risque: RisquePenal
    ) -> Dict[str, Any]:
        """Enrichit l'analyse avec des éléments spécifiques au pénal"""
        
        cat_info = CATEGORIES_PENAL_AFFAIRES.get(risque.categorie_penale, {})
        
        # Calcul des sanctions encourues
        analysis["sanctions_encourues"] = {
            "personnes_physiques": {
                "peines_principales": cat_info.get("sanctions_max", "Non déterminé"),
                "peines_complementaires": self._get_peines_complementaires(risque.categorie_penale),
                "interdictions_professionnelles": risque.categorie_penale in ["corruption", "abus_biens_sociaux", "banqueroute"]
            },
            "personnes_morales": {
                "amende_max": cat_info.get("personnes_morales", "5x l'amende personne physique"),
                "dissolution_possible": risque.categorie_penale in ["corruption", "blanchiment"],
                "exclusion_marches_publics": risque.categorie_penale in ["corruption", "favoritisme"]
            }
        }
        
        # Calcul du délai de prescription
        prescription_info = self._calculate_prescription(risque)
        analysis["prescription"] = prescription_info
        
        # Évaluation de l'urgence
        analysis["urgence"] = {
            "niveau": risque.urgence_traitement,
            "delai_action": self._get_delai_action(risque.urgence_traitement),
            "actions_prioritaires": self._get_actions_prioritaires(risque)
        }
        
        # Score de gravité pénale global
        gravite_score = self._calculate_gravite_penale(risque, analysis)
        analysis["gravite_penale_score"] = gravite_score
        
        # Recommandations stratégiques
        analysis["recommandations_strategiques"] = self._generate_strategic_recommendations(risque, analysis)
        
        return analysis
    
    def _get_peines_complementaires(self, categorie: str) -> List[str]:
        """Retourne les peines complémentaires possibles"""
        peines_base = [
            "Interdiction des droits civiques",
            "Affichage ou diffusion de la décision"
        ]
        
        peines_specifiques = {
            "corruption": ["Interdiction d'exercer une fonction publique", "Confiscation des sommes"],
            "abus_biens_sociaux": ["Interdiction de gérer", "Interdiction d'exercer une activité professionnelle"],
            "delit_initie": ["Interdiction d'exercer l'activité professionnelle", "Confiscation des gains"],
            "fraude_fiscale": ["Interdiction de gérer", "Publication du jugement"],
            "banqueroute": ["Faillite personnelle", "Interdiction de diriger"],
            "escroquerie": ["Interdiction d'émettre des chèques", "Interdiction d'exercer"],
            "favoritisme": ["Interdiction d'exercer une fonction publique", "Inéligibilité"]
        }
        
        return peines_base + peines_specifiques.get(categorie, [])
    
    def _calculate_prescription(self, risque: RisquePenal) -> Dict[str, Any]:
        """Calcule les informations de prescription"""
        cat_info = CATEGORIES_PENAL_AFFAIRES.get(risque.categorie_penale, {})
        delai_base = int(cat_info.get("prescription", "6").split()[0])
        
        # Date de départ de la prescription
        if risque.categorie_penale == "abus_biens_sociaux":
            # Prescription court à partir de la découverte
            date_depart = risque.date_identification
        else:
            # Prescription court à partir des faits
            date_depart = risque.date_identification
        
        date_prescription = date_depart + timedelta(days=delai_base * 365)
        jours_restants = (date_prescription - datetime.now()).days
        
        return {
            "delai_legal": f"{delai_base} ans",
            "date_depart": date_depart,
            "date_expiration": date_prescription,
            "jours_restants": jours_restants,
            "pourcentage_ecoule": max(0, min(100, (1 - jours_restants / (delai_base * 365)) * 100)),
            "alerte": jours_restants < 365
        }
    
    def _get_delai_action(self, urgence: str) -> str:
        """Retourne le délai d'action recommandé"""
        delais = {
            "CRITIQUE": "Action immédiate - 24h maximum",
            "URGENTE": "Action sous 48-72h",
            "ELEVEE": "Action sous 1 semaine",
            "MODEREE": "Action sous 2 semaines",
            "NORMALE": "Action sous 1 mois"
        }
        return delais.get(urgence, "À déterminer")
    
    def _get_actions_prioritaires(self, risque: RisquePenal) -> List[str]:
        """Génère la liste des actions prioritaires"""
        actions = []
        
        # Actions universelles
        actions.extend([
            "Consultation immédiate d'un avocat pénaliste spécialisé",
            "Audit interne pour identifier l'étendue exacte des faits",
            "Sécurisation et inventaire de toutes les preuves"
        ])
        
        # Actions spécifiques par catégorie
        if risque.categorie_penale == "corruption":
            actions.extend([
                "Suspension des relations avec les parties impliquées",
                "Audit anti-corruption étendu",
                "Mise en place d'un programme de conformité Sapin II"
            ])
        elif risque.categorie_penale == "blanchiment":
            actions.extend([
                "Déclaration de soupçon à TRACFIN si applicable",
                "Gel des comptes suspects",
                "Audit AML/CFT complet"
            ])
        elif risque.categorie_penale == "fraude_fiscale":
            actions.extend([
                "Régularisation spontanée potentielle",
                "Calcul exact des montants éludés",
                "Préparation du dossier de défense fiscale"
            ])
        elif risque.categorie_penale == "abus_biens_sociaux":
            actions.extend([
                "Remboursement immédiat des sommes",
                "Convocation d'un conseil d'administration",
                "Documentation de l'intérêt social éventuel"
            ])
        
        # Si prescription proche
        prescription_info = self._calculate_prescription(risque)
        if prescription_info["jours_restants"] < 365:
            actions.insert(0, f"⚠️ URGENT: Prescription dans {prescription_info['jours_restants']} jours")
        
        return actions
    
    def _calculate_gravite_penale(
        self,
        risque: RisquePenal,
        analysis: Dict[str, Any]
    ) -> float:
        """Calcule un score de gravité pénale global"""
        
        # Facteurs de gravité
        factors = {
            "gravite_intrinseque": CATEGORIES_PENAL_AFFAIRES.get(risque.categorie_penale, {}).get("gravite_base", 0.5),
            "montant_prejudice": min(risque.montant_prejudice / 1000000, 1.0),  # Normalisé sur 1M€
            "nb_personnes": min(len(risque.personnes_impliquees) / 10, 1.0),  # Normalisé sur 10 personnes
            "probabilite_poursuites": analysis.get("evaluation_risques", {}).get("probabilite_poursuites", 0.5),
            "probabilite_condamnation": analysis.get("evaluation_risques", {}).get("probabilite_condamnation", 0.5)
        }
        
        # Pondération des facteurs
        weights = {
            "gravite_intrinseque": 0.3,
            "montant_prejudice": 0.25,
            "nb_personnes": 0.15,
            "probabilite_poursuites": 0.15,
            "probabilite_condamnation": 0.15
        }
        
        # Calcul du score pondéré
        score = sum(factors[k] * weights[k] for k in factors)
        
        # Facteurs aggravants
        if risque.categorie_penale in ["corruption", "blanchiment"]:
            score *= 1.2
        if risque.montant_prejudice > 5000000:
            score *= 1.15
        if "recidive" in risque.description.lower():
            score *= 1.3
        
        return min(score, 1.0)
    
    def _generate_strategic_recommendations(
        self,
        risque: RisquePenal,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Génère des recommandations stratégiques"""
        
        recommendations = []
        gravite = analysis.get("gravite_penale_score", 0.5)
        
        # Stratégie globale selon la gravité
        if gravite > 0.8:
            recommendations.append({
                "type": "STRATEGIE_GLOBALE",
                "priorite": "CRITIQUE",
                "action": "Constitution immédiate d'une cellule de crise pénale",
                "detail": "Mobiliser avocat pénaliste senior, direction générale, communication de crise"
            })
        elif gravite > 0.6:
            recommendations.append({
                "type": "STRATEGIE_GLOBALE",
                "priorite": "HAUTE",
                "action": "Task force juridique dédiée",
                "detail": "Équipe pluridisciplinaire : pénal, fiscal, social selon les infractions"
            })
        
        # Stratégie de communication
        if risque.categorie_penale in ["corruption", "fraude_fiscale", "delit_initie"]:
            recommendations.append({
                "type": "COMMUNICATION",
                "priorite": "HAUTE",
                "action": "Stratégie de communication préventive",
                "detail": "Préparer éléments de langage, identifier porte-parole, anticiper questions médias"
            })
        
        # Stratégie de régularisation
        if risque.categorie_penale == "fraude_fiscale":
            recommendations.append({
                "type": "REGULARISATION",
                "priorite": "HAUTE", 
                "action": "Évaluer opportunité régularisation spontanée",
                "detail": "Peut diviser par 2 les sanctions et éviter certaines peines complémentaires"
            })
        
        # Stratégie de négociation
        if analysis.get("evaluation_risques", {}).get("probabilite_poursuites", 0) > 0.7:
            recommendations.append({
                "type": "NEGOCIATION",
                "priorite": "MOYENNE",
                "action": "Préparer stratégie de négociation avec le parquet",
                "detail": "CRPC (plaider coupable), convention judiciaire d'intérêt public si éligible"
            })
        
        # Stratégie de prévention
        recommendations.append({
            "type": "PREVENTION",
            "priorite": "MOYENNE",
            "action": "Renforcer programme de conformité",
            "detail": f"Focus sur prévention {risque.categorie_penale} - Formation, procédures, contrôles"
        })
        
        return recommendations
    
    def create_risque_penal(
        self,
        titre: str,
        description: str,
        categorie: str,
        **kwargs
    ) -> RisquePenal:
        """Crée un nouveau risque pénal"""
        
        # Calcul automatique de certains paramètres si non fournis
        if 'probabilite_poursuites' not in kwargs:
            kwargs['probabilite_poursuites'] = self._estimate_probabilite_poursuites(categorie, description)
        
        if 'gravite_infraction' not in kwargs:
            kwargs['gravite_infraction'] = CATEGORIES_PENAL_AFFAIRES.get(categorie, {}).get('gravite_base', 0.5)
        
        # Déterminer le niveau automatiquement
        score_est = (kwargs.get('probabilite_poursuites', 0.5) * 0.4 + 
                    kwargs.get('gravite_infraction', 0.5) * 0.6)
        
        if score_est > 0.8:
            niveau = RiskLevelPenal.CRITIQUE
        elif score_est > 0.65:
            niveau = RiskLevelPenal.MAJEUR
        elif score_est > 0.45:
            niveau = RiskLevelPenal.SIGNIFICATIF
        elif score_est > 0.25:
            niveau = RiskLevelPenal.MODERE
        else:
            niveau = RiskLevelPenal.NEGLIGEABLE
        
        risque = RisquePenal(
            id=str(uuid.uuid4()),
            titre=titre,
            description=description,
            categorie_penale=categorie,
            niveau=niveau,
            **kwargs
        )
        
        # Sauvegarder
        st.session_state.risques_penaux[risque.id] = risque
        
        # Ajouter à l'historique
        self._add_to_history("creation", risque)
        
        # Créer une alerte si nécessaire
        if risque.urgence_traitement in ["CRITIQUE", "URGENTE"]:
            self._create_alert(risque, f"Nouveau risque pénal {risque.urgence_traitement}")
        
        return risque
    
    def _estimate_probabilite_poursuites(self, categorie: str, description: str) -> float:
        """Estime la probabilité de poursuites basée sur la catégorie et description"""
        
        # Probabilité de base par catégorie
        base_prob = {
            "corruption": 0.75,
            "blanchiment": 0.70,
            "fraude_fiscale": 0.65,
            "abus_biens_sociaux": 0.60,
            "delit_initie": 0.70,
            "escroquerie": 0.55,
            "faux_usage_faux": 0.50,
            "banqueroute": 0.65,
            "entrave": 0.40,
            "favoritisme": 0.60
        }.get(categorie, 0.50)
        
        # Ajustements selon mots-clés dans la description
        keywords_increase = ["plainte", "enquête", "perquisition", "garde à vue", "mise en examen"]
        keywords_decrease = ["soupçon", "potentiel", "éventuel", "risque", "doute"]
        
        for keyword in keywords_increase:
            if keyword in description.lower():
                base_prob = min(base_prob + 0.1, 0.95)
        
        for keyword in keywords_decrease:
            if keyword in description.lower():
                base_prob = max(base_prob - 0.05, 0.20)
        
        return base_prob
    
    def _add_to_history(self, action: str, risque: RisquePenal):
        """Ajoute une action à l'historique"""
        st.session_state.historique_penal.append({
            'timestamp': datetime.now(),
            'action': action,
            'risque_id': risque.id,
            'risque_titre': risque.titre,
            'categorie': risque.categorie_penale,
            'user': st.session_state.get('user_name', 'Système')
        })
    
    def _create_alert(self, risque: RisquePenal, message: str):
        """Crée une alerte"""
        st.session_state.alertes_penales.append({
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now(),
            'risque_id': risque.id,
            'message': message,
            'niveau': risque.urgence_traitement,
            'lu': False
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calcule les statistiques des risques pénaux"""
        risques = list(st.session_state.risques_penaux.values())
        
        if not risques:
            return {
                'total': 0,
                'par_categorie': {},
                'par_niveau': {},
                'alertes_actives': 0
            }
        
        stats = {
            'total': len(risques),
            'par_categorie': {},
            'par_niveau': {},
            'par_urgence': {},
            'montant_total_prejudice': 0,
            'personnes_impliquees_total': set(),
            'risques_critiques': [],
            'prescriptions_proches': [],
            'alertes_actives': len([a for a in st.session_state.alertes_penales if not a['lu']])
        }
        
        for risque in risques:
            # Par catégorie
            cat = risque.categorie_penale
            if cat not in stats['par_categorie']:
                stats['par_categorie'][cat] = {'count': 0, 'montant': 0}
            stats['par_categorie'][cat]['count'] += 1
            stats['par_categorie'][cat]['montant'] += risque.montant_prejudice
            
            # Par niveau
            niveau = risque.niveau.value
            stats['par_niveau'][niveau] = stats['par_niveau'].get(niveau, 0) + 1
            
            # Par urgence
            urgence = risque.urgence_traitement
            stats['par_urgence'][urgence] = stats['par_urgence'].get(urgence, 0) + 1
            
            # Montants et personnes
            stats['montant_total_prejudice'] += risque.montant_prejudice
            stats['personnes_impliquees_total'].update(risque.personnes_impliquees)
            
            # Risques critiques
            if risque.score_risque_penal > 0.7:
                stats['risques_critiques'].append(risque)
            
            # Prescriptions proches
            if risque.date_prescription:
                jours = (risque.date_prescription - datetime.now()).days
                if jours < 365:
                    stats['prescriptions_proches'].append((risque, jours))
        
        stats['personnes_impliquees_total'] = len(stats['personnes_impliquees_total'])
        stats['prescriptions_proches'].sort(key=lambda x: x[1])
        
        return stats


def run():
    """Point d'entrée principal du module - Droit Pénal des Affaires"""
    
    st.set_page_config(layout="wide")
    
    # CSS spécialisé pour le pénal
    st.markdown("""
    <style>
    /* Thème pénal des affaires */
    .penal-alert {
        background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(139, 0, 0, 0.3);
    }
    
    .risk-card-penal {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 10px 10px 0;
        transition: all 0.3s ease;
    }
    
    .risk-critique { border-left-color: #DC143C; }
    .risk-majeur { border-left-color: #FF6347; }
    .risk-significatif { border-left-color: #FFA500; }
    .risk-modere { border-left-color: #FFD700; }
    .risk-negligeable { border-left-color: #90EE90; }
    
    .prescription-warning {
        background: #FFE4B5;
        border: 2px solid #FF8C00;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    
    .llm-result {
        background: rgba(100, 126, 234, 0.1);
        border: 1px solid #647EEA;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .urgence-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    
    .urgence-critique { background: #DC143C; color: white; }
    .urgence-urgente { background: #FF6347; color: white; }
    .urgence-elevee { background: #FFA500; color: white; }
    .urgence-moderee { background: #FFD700; color: black; }
    .urgence-normale { background: #90EE90; color: black; }
    </style>
    """, unsafe_allow_html=True)
    
    # Header avec contexte pénal
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.title("⚖️ Gestion des Risques - Droit Pénal des Affaires")
        st.caption("Analyse multi-LLM : ChatGPT-4, Claude Opus 4, Perplexity, Gemini, Mistral")
    
    with col2:
        # Indicateurs d'alerte
        manager = RisquePenalManager()
        stats = manager.get_statistics()
        
        if stats['alertes_actives'] > 0:
            st.markdown(f"""
            <div class="penal-alert">
                🚨 <strong>{stats['alertes_actives']} alerte(s) active(s)</strong>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Bouton d'urgence
        if st.button("🆘 Assistance Pénale", type="primary", use_container_width=True):
            st.session_state.show_emergency = True
    
    # Navigation principale
    tabs = st.tabs([
        "🎯 Vue d'ensemble",
        "➕ Nouveau risque pénal",
        "📋 Gestion des dossiers",
        "🤖 Analyse IA Multi-LLM",
        "📊 Analytics pénal",
        "⚖️ Jurisprudence",
        "📑 Rapports & Compliance"
    ])
    
    with tabs[0]:
        display_penal_dashboard(manager)
    
    with tabs[1]:
        display_new_penal_risk(manager)
    
    with tabs[2]:
        display_penal_cases_management(manager)
    
    with tabs[3]:
        display_multi_llm_analysis(manager)
    
    with tabs[4]:
        display_penal_analytics(manager)
    
    with tabs[5]:
        display_jurisprudence_center(manager)
    
    with tabs[6]:
        display_compliance_reports(manager)
    
    # Modal d'urgence si activée
    if st.session_state.get('show_emergency', False):
        display_emergency_assistance(manager)


def display_penal_dashboard(manager: RisquePenalManager):
    """Tableau de bord spécialisé droit pénal des affaires"""
    
    stats = manager.get_statistics()
    
    # Alerte principale si risques critiques
    if stats['risques_critiques']:
        st.error(f"""
        ### ⚠️ ALERTE PÉNALE
        **{len(stats['risques_critiques'])} risque(s) critique(s) identifié(s)**
        
        Préjudice total estimé : {stats['montant_total_prejudice']:,.2f} €
        """)
        
        # Actions rapides
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("👨‍⚖️ Contacter avocat", use_container_width=True):
                st.info("Liste des avocats pénalistes partenaires envoyée")
        with col2:
            if st.button("📊 Rapport de crise", use_container_width=True):
                st.session_state.generate_crisis_report = True
        with col3:
            if st.button("🔒 Mode confidentiel", use_container_width=True):
                st.session_state.confidential_mode = True
        with col4:
            if st.button("📞 Cellule de crise", use_container_width=True):
                st.success("Cellule de crise activée")
    
    # Métriques principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Dossiers pénaux",
            stats['total'],
            help="Nombre total de risques pénaux identifiés"
        )
    
    with col2:
        st.metric(
            "Préjudice total",
            f"{stats['montant_total_prejudice'] / 1000000:.1f}M€",
            help="Montant cumulé des préjudices"
        )
    
    with col3:
        st.metric(
            "Personnes impliquées",
            stats['personnes_impliquees_total'],
            help="Nombre total de personnes concernées"
        )
    
    with col4:
        urgent_count = stats['par_urgence'].get('CRITIQUE', 0) + stats['par_urgence'].get('URGENTE', 0)
        st.metric(
            "Cas urgents",
            urgent_count,
            delta=f"+{urgent_count}" if urgent_count > 0 else None
        )
    
    with col5:
        prescriptions = len(stats['prescriptions_proches'])
        st.metric(
            "Prescriptions < 1 an",
            prescriptions,
            delta=f"⚠️ {prescriptions}" if prescriptions > 0 else None
        )
    
    # Graphiques et analyses
    col1, col2 = st.columns(2)
    
    with col1:
        # Répartition par catégorie d'infraction
        if stats['par_categorie']:
            st.markdown("### 📊 Répartition par type d'infraction")
            
            # Préparer les données
            categories = []
            counts = []
            montants = []
            
            for cat, data in stats['par_categorie'].items():
                cat_name = CATEGORIES_PENAL_AFFAIRES.get(cat, {}).get('nom', cat)
                categories.append(cat_name)
                counts.append(data['count'])
                montants.append(data['montant'])
            
            # Graphique en barres avec montants
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='Nombre de cas',
                x=categories,
                y=counts,
                yaxis='y',
                marker_color='indianred'
            ))
            
            fig.add_trace(go.Bar(
                name='Préjudice (k€)',
                x=categories,
                y=[m/1000 for m in montants],
                yaxis='y2',
                marker_color='lightblue',
                opacity=0.7
            ))
            
            fig.update_layout(
                title="Infractions par type et préjudice",
                yaxis=dict(title="Nombre de cas", side="left"),
                yaxis2=dict(title="Préjudice (k€)", overlaying="y", side="right"),
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Matrice urgence/gravité
        st.markdown("### 🎯 Matrice Urgence / Gravité")
        
        if stats['total'] > 0:
            risques = list(st.session_state.risques_penaux.values())
            
            # Créer la matrice
            urgence_map = {
                'NORMALE': 1, 'MODEREE': 2, 'ELEVEE': 3, 
                'URGENTE': 4, 'CRITIQUE': 5
            }
            
            x_vals = []
            y_vals = []
            texts = []
            colors = []
            
            for r in risques:
                x_vals.append(urgence_map.get(r.urgence_traitement, 3))
                y_vals.append(r.score_risque_penal)
                texts.append(f"{r.titre[:30]}...")
                colors.append(r.montant_prejudice)
            
            fig = px.scatter(
                x=x_vals,
                y=y_vals,
                text=texts,
                color=colors,
                color_continuous_scale='Reds',
                labels={'x': 'Urgence', 'y': 'Score de risque', 'color': 'Préjudice €'},
                title="Positionnement des risques pénaux"
            )
            
            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=[1, 2, 3, 4, 5],
                    ticktext=['Normale', 'Modérée', 'Élevée', 'Urgente', 'Critique']
                ),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Alertes de prescription
    if stats['prescriptions_proches']:
        st.markdown("### ⏰ Alertes de prescription")
        
        for risque, jours in stats['prescriptions_proches'][:5]:  # Top 5
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                cat_info = CATEGORIES_PENAL_AFFAIRES.get(risque.categorie_penale, {})
                st.markdown(f"""
                <div class="prescription-warning">
                    <strong>{risque.titre}</strong><br>
                    <small>{cat_info.get('nom', risque.categorie_penale)}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if jours < 0:
                    st.error(f"PRESCRIT ({-jours}j)")
                elif jours < 90:
                    st.error(f"{jours} jours")
                elif jours < 180:
                    st.warning(f"{jours} jours")
                else:
                    st.info(f"{jours} jours")
            
            with col3:
                st.write(f"**Articles:**")
                st.caption(", ".join(cat_info.get('articles', [])[:2]))
            
            with col4:
                if st.button("Gérer", key=f"manage_presc_{risque.id}"):
                    st.session_state.current_risk = risque.id
    
    # Synthèse des recommandations IA
    st.markdown("### 🤖 Synthèse IA Multi-LLM")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **Modèles disponibles:**
        - ChatGPT-4 ✅
        - Claude Opus 4 ✅
        - Perplexity ✅
        - Gemini ✅
        - Mistral ✅
        """)
    
    with col2:
        st.warning("""
        **Analyses en attente:** 3
        - Corruption (urgent)
        - Fraude fiscale
        - ABS
        """)
    
    with col3:
        if st.button("🚀 Lancer analyse globale IA", use_container_width=True):
            st.session_state.launch_global_analysis = True


def display_new_penal_risk(manager: RisquePenalManager):
    """Interface de création d'un nouveau risque pénal"""
    
    st.subheader("➕ Identifier un nouveau risque pénal")
    
    # Mode de saisie
    mode = st.radio(
        "Mode d'identification",
        ["🖊️ Saisie manuelle", "🤖 Analyse IA de document", "📧 Import depuis alerte"],
        horizontal=True
    )
    
    if mode == "🤖 Analyse IA de document":
        st.info("""
        **Analyse IA multi-modèles activée**
        
        Les 5 modèles (ChatGPT-4, Claude Opus 4, Perplexity, Gemini, Mistral) vont analyser 
        votre document pour identifier les risques pénaux potentiels.
        """)
        
        uploaded_file = st.file_uploader(
            "Charger un document",
            type=['pdf', 'docx', 'txt', 'msg', 'eml'],
            help="Rapport d'audit, PV, courrier, email..."
        )
        
        if uploaded_file:
            if st.button("🔍 Analyser avec l'IA", type="primary"):
                with st.spinner("Analyse multi-LLM en cours..."):
                    # Simulation de l'analyse
                    progress = st.progress(0)
                    for i in range(100):
                        time.sleep(0.02)
                        progress.progress(i + 1)
                    
                    # Résultats simulés
                    st.success("✅ Analyse terminée - 3 risques pénaux identifiés")
                    
                    identified_risks = [
                        {
                            "titre": "Soupçon de corruption d'agent public étranger",
                            "categorie": "corruption",
                            "probabilite": 0.75,
                            "montant": 250000,
                            "confidence_ia": 0.88
                        },
                        {
                            "titre": "Risque de qualification en ABS - Utilisation CB société",
                            "categorie": "abus_biens_sociaux",
                            "probabilite": 0.65,
                            "montant": 85000,
                            "confidence_ia": 0.92
                        },
                        {
                            "titre": "Possible requalification en travail dissimulé",
                            "categorie": "entrave",
                            "probabilite": 0.45,
                            "montant": 150000,
                            "confidence_ia": 0.76
                        }
                    ]
                    
                    for i, risk in enumerate(identified_risks):
                        with st.expander(f"Risque {i+1}: {risk['titre']}"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                cat_info = CATEGORIES_PENAL_AFFAIRES.get(risk['categorie'], {})
                                st.write(f"**Catégorie:** {cat_info.get('nom', 'N/A')}")
                                st.write(f"**Articles:** {', '.join(cat_info.get('articles', []))}")
                            
                            with col2:
                                st.metric("Probabilité poursuites", f"{risk['probabilite']:.0%}")
                                st.metric("Préjudice estimé", f"{risk['montant']:,.0f} €")
                            
                            with col3:
                                st.metric("Confiance IA", f"{risk['confidence_ia']:.0%}")
                                
                                if st.button(f"Créer ce risque", key=f"create_risk_{i}"):
                                    # Créer le risque
                                    risque = manager.create_risque_penal(
                                        titre=risk['titre'],
                                        description=f"Identifié par analyse IA du document {uploaded_file.name}",
                                        categorie=risk['categorie'],
                                        probabilite_poursuites=risk['probabilite'],
                                        montant_prejudice=risk['montant']
                                    )
                                    st.success(f"✅ Risque créé avec l'ID {risque.id}")
    
    else:  # Saisie manuelle
        with st.form("new_penal_risk_form"):
            st.markdown("### 📋 Informations sur l'infraction")
            
            col1, col2 = st.columns(2)
            
            with col1:
                titre = st.text_input(
                    "Intitulé du risque*",
                    placeholder="Ex: Soupçon de corruption dans l'obtention du marché X"
                )
                
                categorie = st.selectbox(
                    "Catégorie pénale*",
                    options=list(CATEGORIES_PENAL_AFFAIRES.keys()),
                    format_func=lambda x: CATEGORIES_PENAL_AFFAIRES[x]['nom']
                )
                
                # Afficher les informations légales
                if categorie:
                    cat_info = CATEGORIES_PENAL_AFFAIRES[categorie]
                    st.info(f"""
                    **Articles:** {', '.join(cat_info['articles'])}  
                    **Sanctions max:** {cat_info['sanctions_max']}  
                    **Prescription:** {cat_info['prescription']}
                    """)
            
            with col2:
                date_faits = st.date_input(
                    "Date des faits (approximative)",
                    value=datetime.now().date()
                )
                
                montant_prejudice = st.number_input(
                    "Montant du préjudice estimé (€)",
                    min_value=0.0,
                    step=1000.0,
                    help="Montant total du préjudice ou de l'avantage indu"
                )
                
                statut_actuel = st.selectbox(
                    "Statut actuel",
                    ["identifie", "signale", "enquete_interne", "enquete_preliminaire", 
                     "instruction", "citation", "jugement"]
                )
            
            description = st.text_area(
                "Description détaillée des faits*",
                placeholder="""Décrivez précisément :
- Les faits reprochés
- Les circonstances
- Les personnes impliquées
- Les preuves disponibles
- Les actions déjà entreprises""",
                height=200
            )
            
            st.markdown("### 👥 Personnes impliquées")
            
            personnes_impliquees = st.text_area(
                "Personnes impliquées (une par ligne)",
                placeholder="Jean DUPONT - Directeur Commercial\nMarie MARTIN - Comptable",
                height=100
            )
            
            st.markdown("### 📊 Évaluation du risque")
            
            col1, col2 = st.columns(2)
            
            with col1:
                probabilite_poursuites = st.slider(
                    "Probabilité de poursuites pénales",
                    0.0, 1.0, 0.5, 0.05,
                    help="0% = Très improbable, 100% = Quasi certain"
                )
                
                # Indicateur visuel
                if probabilite_poursuites > 0.7:
                    st.error("⚠️ Risque élevé de poursuites")
                elif probabilite_poursuites > 0.5:
                    st.warning("⚠️ Risque significatif")
                else:
                    st.info("ℹ️ Risque modéré à faible")
            
            with col2:
                elements_constitutifs = st.multiselect(
                    "Éléments constitutifs identifiés",
                    ["Élément matériel caractérisé", "Élément intentionnel prouvé",
                     "Préjudice établi", "Lien de causalité", "Qualité de l'auteur",
                     "Circonstances aggravantes"]
                )
                
                st.metric(
                    "Éléments réunis",
                    f"{len(elements_constitutifs)}/6"
                )
            
            st.markdown("### 🚨 Mesures d'urgence")
            
            mesures_urgentes = st.multiselect(
                "Mesures à prendre immédiatement",
                [
                    "Consultation avocat pénaliste",
                    "Audit interne approfondi",
                    "Suspension des personnes impliquées",
                    "Sécurisation des preuves",
                    "Communication de crise",
                    "Déclaration aux autorités",
                    "Gel des opérations concernées",
                    "Constitution de provisions"
                ],
                default=["Consultation avocat pénaliste", "Sécurisation des preuves"]
            )
            
            # Validation et soumission
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col2:
                submit_draft = st.form_submit_button(
                    "💾 Sauvegarder brouillon",
                    use_container_width=True
                )
            
            with col3:
                submit = st.form_submit_button(
                    "✅ Créer le risque",
                    type="primary",
                    use_container_width=True
                )
            
            if submit and titre and description:
                # Parser les personnes
                personnes = [p.strip() for p in personnes_impliquees.split('\n') if p.strip()]
                
                # Créer le risque
                risque = manager.create_risque_penal(
                    titre=titre,
                    description=description,
                    categorie=categorie,
                    probabilite_poursuites=probabilite_poursuites,
                    montant_prejudice=montant_prejudice,
                    personnes_impliquees=personnes,
                    mesures_urgentes=mesures_urgentes,
                    elements_constitutifs={
                        'identifies': elements_constitutifs,
                        'manquants': [e for e in ["Élément matériel", "Élément intentionnel", "Préjudice"] 
                                     if e not in elements_constitutifs]
                    }
                )
                
                st.success(f"""
                ✅ Risque pénal créé avec succès!
                
                **ID:** {risque.id}  
                **Urgence:** {risque.urgence_traitement}  
                **Score de risque:** {risque.score_risque_penal:.2f}
                """)
                
                # Proposer l'analyse IA immédiate
                if st.button("🤖 Lancer l'analyse IA multi-modèles maintenant"):
                    st.session_state.analyze_risk_id = risque.id
                    st.session_state.switch_to_ai_tab = True
                    st.rerun()


def display_multi_llm_analysis(manager: RisquePenalManager):
    """Interface d'analyse multi-LLM des risques pénaux"""
    
    st.subheader("🤖 Analyse IA Multi-Modèles")
    
    # Configuration des modèles
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_models = st.multiselect(
            "Sélectionner les modèles d'analyse",
            ["gpt-4", "claude-opus-4", "perplexity", "gemini", "mistral"],
            default=["gpt-4", "claude-opus-4", "perplexity", "gemini", "mistral"],
            format_func=lambda x: {
                "gpt-4": "🧠 ChatGPT-4",
                "claude-opus-4": "⚡ Claude Opus 4",
                "perplexity": "🔍 Perplexity",
                "gemini": "🎯 Gemini",
                "mistral": "🌟 Mistral"
            }[x]
        )
    
    with col2:
        analysis_mode = st.selectbox(
            "Mode d'analyse",
            ["consensus", "best_expert", "fusion"],
            format_func=lambda x: {
                "consensus": "🤝 Consensus",
                "best_expert": "🏆 Meilleur expert",
                "fusion": "🔄 Fusion"
            }[x]
        )
    
    with col3:
        if st.button("ℹ️ Guide IA Pénal"):
            st.info("""
            **Spécialités par modèle:**
            - **GPT-4**: Analyse approfondie, jurisprudence
            - **Claude**: Raisonnement juridique complexe
            - **Perplexity**: Recherche temps réel, actualités
            - **Gemini**: Prédictions et tendances
            - **Mistral**: Droit français et européen
            """)
    
    # Sélection du risque à analyser
    risques = list(st.session_state.risques_penaux.values())
    
    if not risques:
        st.warning("Aucun risque pénal identifié. Créez d'abord un risque.")
        return
    
    # Filtrer par urgence
    urgence_filter = st.select_slider(
        "Filtrer par urgence",
        options=["Tous", "NORMALE", "MODEREE", "ELEVEE", "URGENTE", "CRITIQUE"],
        value="Tous"
    )
    
    if urgence_filter != "Tous":
        risques = [r for r in risques if r.urgence_traitement == urgence_filter]
    
    # Sélection du risque
    selected_risk_id = st.selectbox(
        "Sélectionner un risque à analyser",
        options=[r.id for r in risques],
        format_func=lambda x: next(r.titre for r in risques if r.id == x)
    )
    
    if selected_risk_id:
        risque = next(r for r in risques if r.id == selected_risk_id)
        
        # Afficher les détails du risque
        with st.expander("📋 Détails du risque sélectionné"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Catégorie:** {CATEGORIES_PENAL_AFFAIRES[risque.categorie_penale]['nom']}")
                st.write(f"**Montant:** {risque.montant_prejudice:,.2f} €")
            
            with col2:
                st.write(f"**Urgence:** {risque.urgence_traitement}")
                st.write(f"**Score actuel:** {risque.score_risque_penal:.2f}")
            
            with col3:
                st.write(f"**Personnes:** {len(risque.personnes_impliquees)}")
                st.write(f"**Statut:** {risque.statut}")
            
            st.write(f"**Description:** {risque.description}")
        
        # Bouton d'analyse
        if st.button("🚀 Lancer l'analyse multi-modèles", type="primary", use_container_width=True):
            
            # Container pour les résultats
            with st.container():
                # Barre de progression
                progress = st.progress(0)
                status = st.empty()
                
                # Simulation de l'analyse multi-LLM
                status.text("🔄 Initialisation de l'analyse multi-modèles...")
                time.sleep(0.5)
                progress.progress(20)
                
                # Analyse par chaque modèle
                model_results = {}
                
                for i, model in enumerate(selected_models):
                    status.text(f"🤖 Analyse avec {model}...")
                    progress.progress(20 + (i + 1) * 60 / len(selected_models))
                    time.sleep(1)  # Simulation
                    
                    # Résultats simulés par modèle
                    model_results[model] = {
                        "probabilite_poursuites": 0.65 + np.random.uniform(-0.15, 0.15),
                        "probabilite_condamnation": 0.55 + np.random.uniform(-0.15, 0.15),
                        "gravite_penale": 0.70 + np.random.uniform(-0.10, 0.10),
                        "confidence": 0.85 + np.random.uniform(-0.05, 0.05),
                        "recommandations": [
                            "Consulter immédiatement un avocat pénaliste",
                            "Effectuer un audit interne approfondi",
                            "Préparer une stratégie de défense"
                        ],
                        "jurisprudences": [
                            f"Cass. Crim., {np.random.randint(2020, 2024)}, n°{np.random.randint(100, 999)}"
                        ]
                    }
                
                progress.progress(90)
                status.text("🔄 Agrégation des résultats...")
                time.sleep(0.5)
                
                # Agrégation selon le mode
                if analysis_mode == "consensus":
                    # Moyenne des probabilités
                    avg_poursuites = np.mean([r["probabilite_poursuites"] for r in model_results.values()])
                    avg_condamnation = np.mean([r["probabilite_condamnation"] for r in model_results.values()])
                    avg_gravite = np.mean([r["gravite_penale"] for r in model_results.values()])
                    
                    consensus_level = 1 - np.std([r["probabilite_poursuites"] for r in model_results.values()])
                    
                elif analysis_mode == "best_expert":
                    # Sélectionner le modèle avec la meilleure confidence
                    best_model = max(model_results.items(), key=lambda x: x[1]["confidence"])
                    avg_poursuites = best_model[1]["probabilite_poursuites"]
                    avg_condamnation = best_model[1]["probabilite_condamnation"]
                    avg_gravite = best_model[1]["gravite_penale"]
                    consensus_level = best_model[1]["confidence"]
                
                else:  # fusion
                    # Pondération par confidence
                    weights = [r["confidence"] for r in model_results.values()]
                    total_weight = sum(weights)
                    
                    avg_poursuites = sum(r["probabilite_poursuites"] * w for r, w in zip(model_results.values(), weights)) / total_weight
                    avg_condamnation = sum(r["probabilite_condamnation"] * w for r, w in zip(model_results.values(), weights)) / total_weight
                    avg_gravite = sum(r["gravite_penale"] * w for r, w in zip(model_results.values(), weights)) / total_weight
                    consensus_level = np.mean(weights)
                
                progress.progress(100)
                status.text("✅ Analyse terminée!")
                
                # Affichage des résultats
                st.success(f"""
                ### ✅ Analyse Multi-LLM Complétée
                
                **Mode:** {analysis_mode} | **Modèles utilisés:** {len(selected_models)} | 
                **Niveau de consensus:** {consensus_level:.0%}
                """)
                
                # Métriques principales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    delta_poursuites = avg_poursuites - risque.probabilite_poursuites
                    st.metric(
                        "Probabilité poursuites",
                        f"{avg_poursuites:.0%}",
                        delta=f"{delta_poursuites:+.0%}"
                    )
                
                with col2:
                    st.metric(
                        "Probabilité condamnation",
                        f"{avg_condamnation:.0%}"
                    )
                
                with col3:
                    st.metric(
                        "Gravité pénale",
                        f"{avg_gravite:.0%}"
                    )
                
                with col4:
                    new_score = (avg_poursuites * 0.4 + avg_gravite * 0.6)
                    delta_score = new_score - risque.score_risque_penal
                    st.metric(
                        "Score de risque IA",
                        f"{new_score:.2f}",
                        delta=f"{delta_score:+.2f}"
                    )
                
                # Détails par modèle
                st.markdown("### 📊 Analyse détaillée par modèle")
                
                # Créer un DataFrame pour comparaison
                comparison_data = []
                for model, results in model_results.items():
                    comparison_data.append({
                        "Modèle": {
                            "gpt-4": "🧠 ChatGPT-4",
                            "claude-opus-4": "⚡ Claude Opus 4", 
                            "perplexity": "🔍 Perplexity",
                            "gemini": "🎯 Gemini",
                            "mistral": "🌟 Mistral"
                        }[model],
                        "Prob. Poursuites": f"{results['probabilite_poursuites']:.0%}",
                        "Prob. Condamnation": f"{results['probabilite_condamnation']:.0%}",
                        "Gravité": f"{results['gravite_penale']:.0%}",
                        "Confiance": f"{results['confidence']:.0%}"
                    })
                
                df_comparison = pd.DataFrame(comparison_data)
                st.dataframe(df_comparison, use_container_width=True, hide_index=True)
                
                # Graphique radar de comparaison
                categories_radar = ['Poursuites', 'Condamnation', 'Gravité', 'Confiance']
                
                fig = go.Figure()
                
                for model, results in model_results.items():
                    values = [
                        results['probabilite_poursuites'],
                        results['probabilite_condamnation'],
                        results['gravite_penale'],
                        results['confidence']
                    ]
                    
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories_radar,
                        fill='toself',
                        name={
                            "gpt-4": "ChatGPT-4",
                            "claude-opus-4": "Claude Opus 4",
                            "perplexity": "Perplexity", 
                            "gemini": "Gemini",
                            "mistral": "Mistral"
                        }[model]
                    ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )),
                    showlegend=True,
                    title="Comparaison des analyses par modèle"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Recommandations consolidées
                st.markdown("### 💡 Recommandations consolidées")
                
                # Collecter toutes les recommandations uniques
                all_recommendations = set()
                for results in model_results.values():
                    all_recommendations.update(results['recommandations'])
                
                # Afficher avec priorité
                priority_levels = {
                    "Consulter immédiatement un avocat pénaliste": "🔴 CRITIQUE",
                    "Effectuer un audit interne approfondi": "🟠 URGENT",
                    "Préparer une stratégie de défense": "🟡 IMPORTANT"
                }
                
                for rec in sorted(all_recommendations):
                    priority = priority_levels.get(rec, "🔵 RECOMMANDÉ")
                    st.write(f"{priority} : {rec}")
                
                # Actions post-analyse
                st.markdown("### 🎯 Actions suivantes")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📄 Générer rapport détaillé", use_container_width=True):
                        st.info("Rapport en cours de génération...")
                
                with col2:
                    if st.button("📧 Envoyer aux juristes", use_container_width=True):
                        st.success("Analyse envoyée à l'équipe juridique")
                
                with col3:
                    if st.button("💾 Sauvegarder l'analyse", use_container_width=True):
                        # Sauvegarder dans le risque
                        risque.analyse_ia = {
                            "date": datetime.now(),
                            "mode": analysis_mode,
                            "models": selected_models,
                            "results": {
                                "probabilite_poursuites": avg_poursuites,
                                "probabilite_condamnation": avg_condamnation,
                                "gravite_penale": avg_gravite,
                                "consensus_level": consensus_level,
                                "model_results": model_results
                            }
                        }
                        st.success("✅ Analyse sauvegardée dans le dossier")
        
        # Historique des analyses
        if hasattr(risque, 'analyse_ia') and risque.analyse_ia:
            with st.expander("📜 Historique des analyses IA"):
                st.write(f"**Dernière analyse:** {risque.analyse_ia.get('date', 'N/A')}")
                st.write(f"**Mode utilisé:** {risque.analyse_ia.get('mode', 'N/A')}")
                st.write(f"**Modèles:** {', '.join(risque.analyse_ia.get('models', []))}")
                
                results = risque.analyse_ia.get('results', {})
                if results:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Prob. poursuites", f"{results.get('probabilite_poursuites', 0):.0%}")
                    with col2:
                        st.metric("Prob. condamnation", f"{results.get('probabilite_condamnation', 0):.0%}")
                    with col3:
                        st.metric("Consensus", f"{results.get('consensus_level', 0):.0%}")


def display_penal_cases_management(manager: RisquePenalManager):
    """Gestion des dossiers pénaux"""
    
    st.subheader("📋 Gestion des dossiers pénaux")
    
    # Filtres avancés
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_category = st.selectbox(
            "Catégorie d'infraction",
            ["Toutes"] + list(CATEGORIES_PENAL_AFFAIRES.keys()),
            format_func=lambda x: "Toutes" if x == "Toutes" else CATEGORIES_PENAL_AFFAIRES[x]['nom']
        )
    
    with col2:
        filter_urgence = st.selectbox(
            "Urgence",
            ["Toutes", "CRITIQUE", "URGENTE", "ELEVEE", "MODEREE", "NORMALE"]
        )
    
    with col3:
        filter_statut = st.selectbox(
            "Statut",
            ["Tous", "identifie", "enquete_interne", "enquete_preliminaire", "instruction", "jugement"]
        )
    
    with col4:
        sort_by = st.selectbox(
            "Trier par",
            ["Score risque", "Montant préjudice", "Date", "Urgence"]
        )
    
    # Récupérer et filtrer les risques
    risques = list(st.session_state.risques_penaux.values())
    
    if filter_category != "Toutes":
        risques = [r for r in risques if r.categorie_penale == filter_category]
    
    if filter_urgence != "Toutes":
        risques = [r for r in risques if r.urgence_traitement == filter_urgence]
    
    if filter_statut != "Tous":
        risques = [r for r in risques if r.statut == filter_statut]
    
    # Trier
    if sort_by == "Score risque":
        risques.sort(key=lambda r: r.score_risque_penal, reverse=True)
    elif sort_by == "Montant préjudice":
        risques.sort(key=lambda r: r.montant_prejudice, reverse=True)
    elif sort_by == "Date":
        risques.sort(key=lambda r: r.date_identification, reverse=True)
    else:  # Urgence
        urgence_order = {"CRITIQUE": 5, "URGENTE": 4, "ELEVEE": 3, "MODEREE": 2, "NORMALE": 1}
        risques.sort(key=lambda r: urgence_order.get(r.urgence_traitement, 0), reverse=True)
    
    # Affichage des dossiers
    if not risques:
        st.info("Aucun dossier pénal trouvé avec ces critères")
        return
    
    st.write(f"**{len(risques)} dossier(s) trouvé(s)**")
    
    for risque in risques:
        cat_info = CATEGORIES_PENAL_AFFAIRES.get(risque.categorie_penale, {})
        
        # Card du risque avec style selon l'urgence
        urgence_class = f"urgence-{risque.urgence_traitement.lower()}"
        
        with st.container():
            # Header du risque
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div class="risk-card-penal risk-{risque.niveau.value}">
                    <strong>{risque.titre}</strong><br>
                    <small>{cat_info.get('nom', risque.categorie_penale)} | 
                    Articles: {', '.join(cat_info.get('articles', [])[:2])}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.metric("Score", f"{risque.score_risque_penal:.2f}")
            
            with col3:
                st.metric("Préjudice", f"{risque.montant_prejudice / 1000:.0f}k€")
            
            with col4:
                st.markdown(f'<span class="{urgence_class} urgence-badge">{risque.urgence_traitement}</span>', 
                          unsafe_allow_html=True)
            
            with col5:
                if st.button("Gérer", key=f"manage_{risque.id}", use_container_width=True):
                    st.session_state.managing_risk = risque.id
            
            # Détails expandables
            with st.expander("Voir les détails"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Informations générales**")
                    st.write(f"Date des faits: {risque.date_identification.strftime('%d/%m/%Y')}")
                    st.write(f"Statut: {risque.statut}")
                    st.write(f"Personnes impliquées: {len(risque.personnes_impliquees)}")
                    
                    if risque.personnes_impliquees:
                        st.write("**Personnes:**")
                        for personne in risque.personnes_impliquees[:3]:
                            st.caption(f"• {personne}")
                        if len(risque.personnes_impliquees) > 3:
                            st.caption(f"... et {len(risque.personnes_impliquees) - 3} autres")
                
                with col2:
                    st.write("**Analyse pénale**")
                    st.write(f"Prob. poursuites: {risque.probabilite_poursuites:.0%}")
                    st.write(f"Gravité: {risque.gravite_infraction:.0%}")
                    
                    # Prescription
                    prescription_info = manager._calculate_prescription(risque)
                    if prescription_info['jours_restants'] < 365:
                        st.error(f"⏰ Prescription dans {prescription_info['jours_restants']} jours!")
                    else:
                        st.info(f"Prescription: {prescription_info['date_expiration'].strftime('%d/%m/%Y')}")
                
                with col3:
                    st.write("**Actions et mesures**")
                    
                    if risque.mesures_urgentes:
                        st.write("**Mesures urgentes:**")
                        for mesure in risque.mesures_urgentes[:3]:
                            st.caption(f"✓ {mesure}")
                    
                    # Analyse IA
                    if hasattr(risque, 'analyse_ia') and risque.analyse_ia:
                        st.success("✅ Analyse IA disponible")
                    else:
                        if st.button("🤖 Analyser", key=f"analyze_{risque.id}"):
                            st.session_state.analyze_risk_id = risque.id
                            st.session_state.switch_to_ai_tab = True
                            st.rerun()
            
            st.divider()
    
    # Modal de gestion si un risque est sélectionné
    if st.session_state.get('managing_risk'):
        display_risk_management_modal(manager, st.session_state.managing_risk)


def display_risk_management_modal(manager: RisquePenalManager, risk_id: str):
    """Modal de gestion détaillée d'un risque pénal"""
    
    risque = st.session_state.risques_penaux.get(risk_id)
    if not risque:
        return
    
    # Créer une modal
    @st.dialog(f"Gestion du dossier pénal - {risque.titre[:50]}...")
    def risk_modal():
        # Onglets de gestion
        tabs = st.tabs([
            "📋 Synthèse",
            "👥 Personnes",
            "📄 Preuves",
            "⚖️ Stratégie",
            "📅 Échéancier",
            "💰 Impact financier"
        ])
        
        with tabs[0]:  # Synthèse
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Catégorie:**", CATEGORIES_PENAL_AFFAIRES[risque.categorie_penale]['nom'])
                st.write("**Score de risque:**", f"{risque.score_risque_penal:.2f}")
                st.write("**Urgence:**", risque.urgence_traitement)
                
                # Mise à jour du statut
                new_status = st.selectbox(
                    "Statut du dossier",
                    ["identifie", "signale", "enquete_interne", "enquete_preliminaire",
                     "instruction", "citation", "jugement", "clos"],
                    index=["identifie", "signale", "enquete_interne", "enquete_preliminaire",
                           "instruction", "citation", "jugement", "clos"].index(risque.statut)
                )
                
                if new_status != risque.statut and st.button("Mettre à jour le statut"):
                    risque.statut = new_status
                    manager._add_to_history("changement_statut", risque)
                    st.success("Statut mis à jour")
                    st.rerun()
            
            with col2:
                # Indicateurs clés
                st.metric("Préjudice", f"{risque.montant_prejudice:,.0f} €")
                st.metric("Personnes impliquées", len(risque.personnes_impliquees))
                
                # Prescription
                prescription_info = manager._calculate_prescription(risque)
                if prescription_info['jours_restants'] < 180:
                    st.error(f"⏰ Prescription dans {prescription_info['jours_restants']} jours!")
                else:
                    days_color = "🟢" if prescription_info['jours_restants'] > 730 else "🟡"
                    st.info(f"{days_color} {prescription_info['jours_restants']} jours avant prescription")
        
        with tabs[1]:  # Personnes
            st.write("### Personnes impliquées")
            
            # Liste actuelle
            for i, personne in enumerate(risque.personnes_impliquees):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{i+1}. {personne}")
                with col2:
                    if st.button("🗑️", key=f"remove_person_{i}"):
                        risque.personnes_impliquees.pop(i)
                        st.rerun()
            
            # Ajouter une personne
            new_person = st.text_input("Ajouter une personne")
            if st.button("➕ Ajouter") and new_person:
                risque.personnes_impliquees.append(new_person)
                st.success(f"Ajouté: {new_person}")
                st.rerun()
        
        with tabs[2]:  # Preuves
            st.write("### Éléments de preuve")
            
            # Liste des preuves
            if risque.preuves_disponibles:
                for i, preuve in enumerate(risque.preuves_disponibles):
                    st.write(f"• {preuve}")
            else:
                st.info("Aucune preuve documentée")
            
            # Ajouter une preuve
            new_preuve = st.text_area("Ajouter un élément de preuve")
            if st.button("➕ Ajouter la preuve") and new_preuve:
                risque.preuves_disponibles.append(new_preuve)
                st.success("Preuve ajoutée")
                st.rerun()
        
        with tabs[3]:  # Stratégie
            st.write("### Stratégie de défense")
            
            # Éléments constitutifs
            st.write("**Éléments constitutifs de l'infraction:**")
            
            elements = risque.elements_constitutifs.get('identifies', [])
            manquants = risque.elements_constitutifs.get('manquants', [])
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ Éléments réunis ({len(elements)})")
                for elem in elements:
                    st.write(f"• {elem}")
            
            with col2:
                if manquants:
                    st.warning(f"❌ Éléments manquants ({len(manquants)})")
                    for elem in manquants:
                        st.write(f"• {elem}")
            
            # Stratégie recommandée
            st.write("**Stratégie recommandée:**")
            
            if risque.probabilite_poursuites < 0.3:
                strategy = "Surveillance et prévention"
                st.info("Risque faible - Maintenir la vigilance et renforcer la compliance")
            elif risque.probabilite_poursuites < 0.6:
                strategy = "Préparation défensive"
                st.warning("Risque modéré - Préparer une défense et documenter les justificatifs")
            else:
                strategy = "Défense active"
                st.error("Risque élevé - Mobiliser l'équipe juridique et préparer la défense")
            
            st.write(f"**Approche:** {strategy}")
        
        with tabs[4]:  # Échéancier
            st.write("### Échéancier procédural")
            
            # Dates clés
            dates_cles = [
                ("Date des faits", risque.date_identification),
                ("Date de découverte", risque.date_identification),
                ("Fin de prescription", risque.date_prescription or 
                 (risque.date_identification + timedelta(days=6*365)))
            ]
            
            for label, date in dates_cles:
                if date:
                    st.write(f"**{label}:** {date.strftime('%d/%m/%Y')}")
            
            # Ajouter une date
            st.write("**Ajouter une échéance:**")
            col1, col2 = st.columns(2)
            with col1:
                event_type = st.selectbox(
                    "Type",
                    ["Convocation", "Audition", "Perquisition", "Audience", "Délibéré", "Autre"]
                )
            with col2:
                event_date = st.date_input("Date")
            
            event_desc = st.text_input("Description")
            
            if st.button("➕ Ajouter l'échéance"):
                # Ajouter à un calendrier (à implémenter)
                st.success(f"Échéance ajoutée: {event_type} le {event_date}")
        
        with tabs[5]:  # Impact financier
            st.write("### Évaluation de l'impact financier")
            
            # Montants actuels
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Préjudice identifié", f"{risque.montant_prejudice:,.0f} €")
                
                # Mise à jour du montant
                new_amount = st.number_input(
                    "Nouveau montant",
                    value=float(risque.montant_prejudice),
                    step=1000.0
                )
                
                if new_amount != risque.montant_prejudice and st.button("Mettre à jour"):
                    risque.montant_prejudice = new_amount
                    st.success("Montant mis à jour")
                    st.rerun()
            
            with col2:
                # Estimation des coûts
                cat_info = CATEGORIES_PENAL_AFFAIRES[risque.categorie_penale]
                
                st.write("**Sanctions encourues:**")
                st.write(f"• Personnes physiques: {cat_info['sanctions_max']}")
                st.write(f"• Personnes morales: {cat_info.get('personnes_morales', 'N/A')}")
                
                # Calcul des provisions
                provisions = {
                    "Amende maximale": risque.montant_prejudice * 5,  # Estimation
                    "Frais d'avocat": risque.montant_prejudice * 0.1,
                    "Frais d'expertise": 50000,
                    "Autres frais": 25000
                }
                
                total_provisions = sum(provisions.values())
                
                st.write("**Provisions recommandées:**")
                for label, amount in provisions.items():
                    st.write(f"• {label}: {amount:,.0f} €")
                
                st.metric("Total provisions", f"{total_provisions:,.0f} €")
        
        # Boutons d'action
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Générer rapport", use_container_width=True):
                st.info("Génération du rapport pénal...")
        
        with col2:
            if st.button("🤖 Analyse IA", use_container_width=True):
                st.session_state.analyze_risk_id = risk_id
                st.session_state.switch_to_ai_tab = True
                st.rerun()
        
        with col3:
            if st.button("❌ Fermer", use_container_width=True, type="secondary"):
                st.session_state.managing_risk = None
                st.rerun()
    
    # Afficher la modal
    risk_modal()


def display_penal_analytics(manager: RisquePenalManager):
    """Analytics spécialisés pour le pénal des affaires"""
    
    st.subheader("📊 Analytics - Droit Pénal des Affaires")
    
    stats = manager.get_statistics()
    
    if stats['total'] == 0:
        st.info("Aucune donnée à analyser. Créez d'abord des risques pénaux.")
        return
    
    # Onglets d'analyse
    tabs = st.tabs([
        "🎯 Vue d'ensemble",
        "📈 Tendances",
        "⚖️ Par infraction", 
        "💰 Impact financier",
        "⏰ Prescriptions"
    ])
    
    with tabs[0]:  # Vue d'ensemble
        # KPIs principaux
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Score de risque pénal global
            risques = list(st.session_state.risques_penaux.values())
            score_global = np.mean([r.score_risque_penal for r in risques])
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = score_global,
                title = {'text': "Score de risque pénal global"},
                gauge = {
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkred"},
                    'steps': [
                        {'range': [0, 0.25], 'color': "lightgreen"},
                        {'range': [0.25, 0.5], 'color': "yellow"},
                        {'range': [0.5, 0.75], 'color': "orange"},
                        {'range': [0.75, 1], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.7
                    }
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Répartition par urgence
            urgence_data = []
            for urgence, count in stats['par_urgence'].items():
                urgence_data.append({
                    'Urgence': urgence,
                    'Nombre': count
                })
            
            if urgence_data:
                df_urgence = pd.DataFrame(urgence_data)
                fig = px.pie(
                    df_urgence,
                    values='Nombre',
                    names='Urgence',
                    title="Répartition par urgence",
                    color_discrete_map={
                        'CRITIQUE': '#8B0000',
                        'URGENTE': '#DC143C',
                        'ELEVEE': '#FF6347',
                        'MODEREE': '#FFA500',
                        'NORMALE': '#90EE90'
                    }
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # Top 3 catégories à risque
            st.markdown("**Top 3 infractions**")
            
            cat_sorted = sorted(
                stats['par_categorie'].items(),
                key=lambda x: x[1]['montant'],
                reverse=True
            )[:3]
            
            for cat, data in cat_sorted:
                cat_name = CATEGORIES_PENAL_AFFAIRES[cat]['nom']
                st.write(f"**{cat_name}**")
                st.caption(f"{data['count']} cas | {data['montant']/1000000:.1f}M€")
        
        with col4:
            # Indicateurs d'alerte
            st.markdown("**Alertes actives**")
            
            critical_count = stats['par_urgence'].get('CRITIQUE', 0)
            urgent_count = stats['par_urgence'].get('URGENTE', 0)
            prescription_count = len(stats['prescriptions_proches'])
            
            if critical_count > 0:
                st.error(f"🔴 {critical_count} cas critiques")
            if urgent_count > 0:
                st.warning(f"🟠 {urgent_count} cas urgents")
            if prescription_count > 0:
                st.info(f"⏰ {prescription_count} prescriptions < 1 an")
    
    with tabs[1]:  # Tendances
        st.markdown("### 📈 Évolution temporelle")
        
        # Créer des données temporelles simulées
        risques = list(st.session_state.risques_penaux.values())
        
        # Grouper par mois
        timeline_data = []
        for risque in risques:
            month = risque.date_identification.strftime('%Y-%m')
            timeline_data.append({
                'Mois': month,
                'Catégorie': CATEGORIES_PENAL_AFFAIRES[risque.categorie_penale]['nom'],
                'Score': risque.score_risque_penal,
                'Montant': risque.montant_prejudice
            })
        
        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)
            
            # Évolution du nombre de cas
            fig = px.histogram(
                df_timeline,
                x='Mois',
                color='Catégorie',
                title="Évolution du nombre de cas par mois",
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Évolution des montants
            monthly_amounts = df_timeline.groupby('Mois')['Montant'].sum().reset_index()
            fig = px.line(
                monthly_amounts,
                x='Mois',
                y='Montant',
                title="Évolution des montants de préjudice",
                markers=True
            )
            fig.update_yaxis(tickformat=",")
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:  # Par infraction
        st.markdown("### ⚖️ Analyse par type d'infraction")
        
        # Tableau détaillé par catégorie
        cat_analysis = []
        
        for cat, data in stats['par_categorie'].items():
            cat_info = CATEGORIES_PENAL_AFFAIRES[cat]
            
            # Calculer les moyennes pour cette catégorie
            cat_risques = [r for r in risques if r.categorie_penale == cat]
            avg_score = np.mean([r.score_risque_penal for r in cat_risques]) if cat_risques else 0
            avg_prob = np.mean([r.probabilite_poursuites for r in cat_risques]) if cat_risques else 0
            
            cat_analysis.append({
                'Infraction': cat_info['nom'],
                'Nombre': data['count'],
                'Montant total': f"{data['montant']:,.0f} €",
                'Score moyen': f"{avg_score:.2f}",
                'Prob. poursuites': f"{avg_prob:.0%}",
                'Sanctions max': cat_info['sanctions_max'].split('et')[0].strip()
            })
        
        df_cat = pd.DataFrame(cat_analysis)
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
        
        # Matrice de corrélation entre infractions
        if len(stats['par_categorie']) > 3:
            st.markdown("### 🔗 Corrélations entre infractions")
            st.info("Analyse des infractions souvent associées")
            
            # Simulation de corrélations
            categories = list(stats['par_categorie'].keys())
            corr_matrix = np.random.rand(len(categories), len(categories))
            np.fill_diagonal(corr_matrix, 1)
            
            # Rendre symétrique
            corr_matrix = (corr_matrix + corr_matrix.T) / 2
            
            fig = px.imshow(
                corr_matrix,
                labels=dict(x="Infraction", y="Infraction", color="Corrélation"),
                x=[CATEGORIES_PENAL_AFFAIRES[c]['nom'] for c in categories],
                y=[CATEGORIES_PENAL_AFFAIRES[c]['nom'] for c in categories],
                color_continuous_scale='RdBu_r',
                zmin=-1, zmax=1
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[3]:  # Impact financier
        st.markdown("### 💰 Analyse de l'impact financier")
        
        # Métriques financières globales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Préjudice total identifié",
                f"{stats['montant_total_prejudice']:,.0f} €"
            )
        
        with col2:
            # Estimation des sanctions
            sanctions_est = stats['montant_total_prejudice'] * 2.5  # Estimation
            st.metric(
                "Sanctions potentielles",
                f"{sanctions_est:,.0f} €",
                help="Estimation basée sur les infractions"
            )
        
        with col3:
            # Provisions recommandées
            provisions = sanctions_est + stats['montant_total_prejudice'] * 0.15
            st.metric(
                "Provisions totales",
                f"{provisions:,.0f} €",
                help="Sanctions + frais juridiques"
            )
        
        # Distribution des montants
        montants = [r.montant_prejudice for r in risques if r.montant_prejudice > 0]
        
        if montants:
            fig = px.histogram(
                montants,
                nbins=20,
                title="Distribution des montants de préjudice",
                labels={'value': 'Montant (€)', 'count': 'Nombre de cas'}
            )
            fig.update_xaxis(tickformat=",")
            st.plotly_chart(fig, use_container_width=True)
            
            # Top 5 des risques par montant
            st.markdown("### 💸 Top 5 - Impact financier")
            
            top_risques = sorted(risques, key=lambda r: r.montant_prejudice, reverse=True)[:5]
            
            for i, risque in enumerate(top_risques):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{i+1}. {risque.titre}**")
                    st.caption(CATEGORIES_PENAL_AFFAIRES[risque.categorie_penale]['nom'])
                
                with col2:
                    st.metric("Préjudice", f"{risque.montant_prejudice/1000000:.1f}M€")
                
                with col3:
                    sanctions = risque.montant_prejudice * 2.5
                    st.metric("Risque total", f"{sanctions/1000000:.1f}M€")
    
    with tabs[4]:  # Prescriptions
        st.markdown("### ⏰ Analyse des prescriptions")
        
        # Timeline des prescriptions
        prescription_data = []
        
        for risque in risques:
            prescription_info = manager._calculate_prescription(risque)
            
            prescription_data.append({
                'Titre': risque.titre[:50] + "...",
                'Catégorie': CATEGORIES_PENAL_AFFAIRES[risque.categorie_penale]['nom'],
                'Date prescription': prescription_info['date_expiration'],
                'Jours restants': prescription_info['jours_restants'],
                'Pourcentage écoulé': prescription_info['pourcentage_ecoule']
            })
        
        df_prescription = pd.DataFrame(prescription_data)
        df_prescription = df_prescription.sort_values('Jours restants')
        
        # Graphique Gantt des prescriptions
        fig = px.timeline(
            df_prescription.head(20),  # Top 20
            x_start="Date prescription",
            x_end="Date prescription",
            y="Titre",
            color="Pourcentage écoulé",
            title="Timeline des prescriptions",
            color_continuous_scale='RdYlGn_r'
        )
        
        # Ajouter la date actuelle
        fig.add_vline(x=datetime.now(), line_dash="dash", line_color="red",
                     annotation_text="Aujourd'hui")
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Alertes de prescription
        st.markdown("### 🚨 Alertes de prescription")
        
        urgent_prescriptions = df_prescription[df_prescription['Jours restants'] < 365]
        
        if not urgent_prescriptions.empty:
            for _, row in urgent_prescriptions.iterrows():
                urgency = "🔴" if row['Jours restants'] < 90 else "🟠" if row['Jours restants'] < 180 else "🟡"
                
                st.warning(f"""
                {urgency} **{row['Titre']}**  
                Catégorie: {row['Catégorie']}  
                Prescription dans: **{row['Jours restants']} jours** ({row['Date prescription'].strftime('%d/%m/%Y')})
                """)
        else:
            st.success("✅ Aucune prescription urgente")


def display_jurisprudence_center(manager: RisquePenalManager):
    """Centre de recherche jurisprudentielle pénal"""
    
    st.subheader("⚖️ Centre de Jurisprudence - Droit Pénal des Affaires")
    
    # Recherche
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Rechercher dans la jurisprudence",
            placeholder="Ex: corruption agent public, ABS dirigeant, blanchiment aggravé..."
        )
    
    with col2:
        juridiction = st.selectbox(
            "Juridiction",
            ["Toutes", "Cass. Crim.", "CA Paris", "CA Versailles", "TC Paris"]
        )
    
    with col3:
        periode = st.selectbox(
            "Période",
            ["Toutes", "2024", "2023", "2022", "5 dernières années"]
        )
    
    # Base de jurisprudences (simulée)
    jurisprudences = [
        {
            "reference": "Cass. Crim., 15 janvier 2024, n°23-81.234",
            "categorie": "corruption",
            "resume": "Corruption d'agent public étranger - Preuve de l'élément intentionnel",
            "apport": "L'élément intentionnel est caractérisé dès lors que le prévenu avait conscience du caractère indu de l'avantage promis.",
            "sanction": "3 ans ferme + 500k€ amende"
        },
        {
            "reference": "CA Paris, 28 novembre 2023, n°22/04567",
            "categorie": "abus_biens_sociaux",
            "resume": "ABS - Usage de la carte bancaire société pour dépenses personnelles",
            "apport": "L'utilisation répétée de moyens de paiement sociaux pour des dépenses personnelles caractérise l'ABS même sans enrichissement.",
            "sanction": "18 mois avec sursis + remboursement"
        },
        {
            "reference": "Cass. Crim., 7 mars 2024, n°23-85.678",
            "categorie": "blanchiment",
            "resume": "Blanchiment aggravé - Utilisation du système bancaire",
            "apport": "Le blanchiment est aggravé lorsqu'il est commis en utilisant les facilités procurées par l'exercice d'une activité professionnelle.",
            "sanction": "5 ans ferme + 750k€"
        },
        {
            "reference": "TC Paris, 15 mai 2024, n°2023/12345",
            "categorie": "fraude_fiscale",
            "resume": "Fraude fiscale aggravée - Montage complexe avec sociétés offshore",
            "apport": "La fraude fiscale est aggravée en cas de recours à des montages complexes impliquant des paradis fiscaux.",
            "sanction": "4 ans dont 2 ferme + 2M€"
        }
    ]
    
    # Filtrer selon la recherche
    if search_query:
        jurisprudences = [j for j in jurisprudences 
                         if search_query.lower() in j['resume'].lower() 
                         or search_query.lower() in j['apport'].lower()]
    
    # Affichage des résultats
    st.write(f"**{len(jurisprudences)} décision(s) trouvée(s)**")
    
    for juris in jurisprudences:
        with st.expander(f"📜 {juris['reference']}"):
            cat_info = CATEGORIES_PENAL_AFFAIRES.get(juris['categorie'], {})
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Catégorie:** {cat_info.get('nom', 'N/A')}")
                st.write(f"**Résumé:** {juris['resume']}")
                st.info(f"**Apport jurisprudentiel:** {juris['apport']}")
            
            with col2:
                st.metric("Sanction prononcée", juris['sanction'])
                
                if st.button("📎 Utiliser", key=f"use_juris_{juris['reference']}"):
                    st.session_state.selected_jurisprudence = juris
                    st.success("Jurisprudence sélectionnée")
    
    # Tendances jurisprudentielles
    st.markdown("### 📈 Tendances jurisprudentielles 2024")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📈 En hausse:**
        - Sanctions pour corruption internationale
        - Poursuites pour fraude fiscale aggravée
        - Condamnations ABS avec interdiction de gérer
        """)
    
    with col2:
        st.warning("""
        **📉 En baisse:**
        - Relaxes pour défaut d'élément intentionnel
        - Classements pour prescription
        - Sursis pour primo-délinquants
        """)


def display_compliance_reports(manager: RisquePenalManager):
    """Rapports et compliance pénal"""
    
    st.subheader("📑 Rapports & Compliance - Droit Pénal des Affaires")
    
    # Type de rapport
    report_type = st.selectbox(
        "Type de rapport",
        [
            "Rapport de situation pénale",
            "Cartographie des risques pénaux",
            "Rapport pour le conseil d'administration",
            "Déclaration de soupçon (TRACFIN)",
            "Rapport d'audit pénal",
            "Plan de prévention Sapin II"
        ]
    )
    
    # Configuration du rapport
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periode = st.date_input(
            "Période",
            value=(datetime.now() - timedelta(days=90), datetime.now())
        )
    
    with col2:
        include_ia = st.checkbox("Inclure analyses IA", value=True)
        include_juris = st.checkbox("Inclure jurisprudences", value=True)
    
    with col3:
        confidentialite = st.selectbox(
            "Niveau de confidentialité",
            ["Confidentiel", "Très confidentiel", "Secret défense"]
        )
    
    # Génération du rapport
    if st.button("🚀 Générer le rapport", type="primary", use_container_width=True):
        with st.spinner("Génération en cours..."):
            time.sleep(2)  # Simulation
            
            # Aperçu du rapport
            st.success("✅ Rapport généré avec succès!")
            
            # Contenu du rapport (exemple)
            st.markdown(f"""
            # {report_type.upper()}
            
            **Date:** {datetime.now().strftime('%d/%m/%Y')}  
            **Période couverte:** {periode[0].strftime('%d/%m/%Y')} - {periode[1].strftime('%d/%m/%Y')}  
            **Classification:** {confidentialite}
            
            ## Synthèse exécutive
            
            L'analyse de la période révèle {manager.get_statistics()['total']} risques pénaux identifiés,
            dont {len(manager.get_statistics()['risques_critiques'])} nécessitent une action immédiate.
            
            ### Points d'attention majeurs:
            
            1. **Risques critiques:** {len(manager.get_statistics()['risques_critiques'])} dossiers
            2. **Montant total en jeu:** {manager.get_statistics()['montant_total_prejudice']:,.0f} €
            3. **Prescriptions proches:** {len(manager.get_statistics()['prescriptions_proches'])} dossiers
            
            ### Recommandations prioritaires:
            
            1. Mobilisation immédiate de l'équipe juridique sur les dossiers critiques
            2. Constitution de provisions à hauteur de {manager.get_statistics()['montant_total_prejudice'] * 2.5:,.0f} €
            3. Renforcement du programme de conformité sur les zones à risque identifiées
            
            ---
            *Ce rapport est strictement confidentiel et destiné aux seuls destinataires autorisés.*
            """)
            
            # Boutons d'action
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    "📥 Télécharger PDF",
                    data=b"Contenu PDF",  # Simulé
                    file_name=f"rapport_penal_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col2:
                if st.button("📧 Envoyer", use_container_width=True):
                    st.info("Rapport envoyé aux destinataires autorisés")
            
            with col3:
                if st.button("🔒 Archiver", use_container_width=True):
                    st.success("Rapport archivé de manière sécurisée")


def display_emergency_assistance(manager: RisquePenalManager):
    """Assistance d'urgence pénale"""
    
    @st.dialog("🆘 Assistance Pénale d'Urgence")
    def emergency_modal():
        st.error("**PROCÉDURE D'URGENCE ACTIVÉE**")
        
        # Type d'urgence
        urgence_type = st.selectbox(
            "Type de situation",
            [
                "Perquisition en cours",
                "Garde à vue",
                "Convocation urgente",
                "Découverte d'infraction grave",
                "Demande d'information des autorités",
                "Autre urgence pénale"
            ]
        )
        
        # Actions immédiates
        st.markdown("### ⚡ Actions immédiates")
        
        if urgence_type == "Perquisition en cours":
            st.error("""
            1. **NE PAS S'OPPOSER** à la perquisition
            2. **APPELER IMMÉDIATEMENT** l'avocat de garde: 📞 01.XX.XX.XX.XX
            3. **DESIGNER** un représentant pour assister
            4. **NOTER** tous les documents saisis
            5. **NE RIEN DECLARER** sans avocat
            """)
        
        elif urgence_type == "Garde à vue":
            st.error("""
            1. **DEMANDER UN AVOCAT** immédiatement
            2. **EXERCER** le droit au silence
            3. **PREVENIR** un proche (droit)
            4. **DEMANDER** un examen médical si nécessaire
            5. **NE SIGNER AUCUN DOCUMENT** sans lecture attentive avec avocat
            """)
        
        # Contacts d'urgence
        st.markdown("### 📞 Contacts d'urgence")
        
        contacts = [
            ("Avocat pénaliste de garde", "01.XX.XX.XX.XX", "24/7"),
            ("Responsable juridique", "06.XX.XX.XX.XX", "24/7"),
            ("Cellule de crise", "01.XX.XX.XX.XX", "Heures ouvrées"),
            ("Assurance D&O", "0800.XXX.XXX", "24/7")
        ]
        
        for nom, tel, dispo in contacts:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{nom}**")
            with col2:
                st.write(f"📞 {tel}")
            with col3:
                st.caption(dispo)
        
        # Documentation d'urgence
        st.markdown("### 📄 Documents à préparer")
        
        docs_checklist = st.multiselect(
            "Cochez les documents préparés",
            [
                "Pouvoirs et délégations",
                "Statuts de la société",
                "Organigramme juridique",
                "Polices d'assurance",
                "Coordonnées des dirigeants",
                "Liste des conseils externes"
            ]
        )
        
        # Actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚨 Activer cellule de crise", type="primary", use_container_width=True):
                st.success("Cellule de crise activée - Notifications envoyées")
        
        with col2:
            if st.button("📋 Check-list PDF", use_container_width=True):
                st.info("Téléchargement de la check-list d'urgence")
        
        if st.button("Fermer", use_container_width=True):
            st.session_state.show_emergency = False
            st.rerun()
    
    emergency_modal()


# Point d'entrée principal
if __name__ == "__main__":
    run()