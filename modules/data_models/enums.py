"""Enumerations extracted from dataclasses.py for better organization."""
from enum import Enum


class RiskLevel(Enum):
    """Niveaux de risque"""
    FAIBLE = "faible"
    MOYEN = "moyen"
    ELEVE = "élevé"
    CRITIQUE = "critique"

    def to_int(self) -> int:
        mapping = {
            self.FAIBLE: 1,
            self.MOYEN: 2,
            self.ELEVE: 3,
            self.CRITIQUE: 4,
        }
        return mapping.get(self, 2)


class SourceJurisprudence(Enum):
    """Sources de jurisprudence disponibles"""
    LEGIFRANCE = "legifrance"
    JUDILIBRE = "judilibre"
    DOCTRINE = "doctrine"
    DALLOZ = "dalloz"
    LEXIS = "lexis"
    INTERNAL = "internal"
    MANUAL = "manual"
    COURDECASSATION = "courdecassation"
    CONSEILDETAT = "conseildetat"
    CONSEILCONSTITUTIONNEL = "conseilconstitutionnel"


class SourceEntreprise(Enum):
    """Sources d'information sur les entreprises"""
    PAPPERS = "pappers"
    SOCIETE_COM = "societe.com"
    INFOGREFFE = "infogreffe"
    INSEE = "insee"
    MANUAL = "manual"
    CACHED = "cached"


class TypeJuridiction(Enum):
    """Types de juridictions"""
    COUR_DE_CASSATION = "Cour de cassation"
    CONSEIL_ETAT = "Conseil d'État"
    CONSEIL_CONSTITUTIONNEL = "Conseil constitutionnel"
    COUR_APPEL = "Cour d'appel"
    TRIBUNAL_JUDICIAIRE = "Tribunal judiciaire"
    TRIBUNAL_COMMERCE = "Tribunal de commerce"
    TRIBUNAL_ADMINISTRATIF = "Tribunal administratif"
    COUR_ADMINISTRATIVE_APPEL = "Cour administrative d'appel"
    TRIBUNAL_CORRECTIONNEL = "Tribunal correctionnel"
    COUR_ASSISES = "Cour d'assises"
    CONSEIL_PRUDHOMMES = "Conseil de prud'hommes"
    TRIBUNAL_POLICE = "Tribunal de police"
    JURIDICTION_PROXIMITE = "Juridiction de proximité"
    JUGE_INSTRUCTION = "Juge d'instruction"
    PROCUREUR = "Procureur de la République"
    TRIBUNAL = "Tribunal"
    AUTRE = "Autre"


class StatutProcedural(Enum):
    """Statut d'une personne dans la procédure pénale"""
    SUSPECT = "suspect"
    MIS_EN_CAUSE = "mis en cause"
    TEMOIN = "témoin"
    VICTIME = "victime"
    MIS_EN_EXAMEN = "mis en examen"
    TEMOIN_ASSISTE = "témoin assisté"
    PARTIE_CIVILE = "partie civile"
    PREVENU = "prévenu"
    ACCUSE = "accusé"
    CONDAMNE = "condamné"
    RELAXE = "relaxé"
    PLAIGNANT = "plaignant"
    CIVILEMENT_RESPONSABLE = "civilement responsable"
    TIERS = "tiers"
    ACTIF = "actif"
    INACTIF = "inactif"
    DESISTE = "désisté"
    INTERVENANT = "intervenant"


class PhaseProcedure(Enum):
    """Phase de la procédure pénale"""
    ENQUETE_PRELIMINAIRE = "enquête préliminaire"
    ENQUETE_FLAGRANCE = "enquête de flagrance"
    INSTRUCTION = "instruction"
    JUGEMENT = "jugement"
    APPEL = "appel"
    CASSATION = "cassation"
    EXECUTION = "exécution"
    PRE_CONTENTIEUX = "pré-contentieux"
    PREMIERE_INSTANCE = "première instance"


class SearchMode(Enum):
    """Modes de recherche"""
    SIMPLE = "simple"
    ADVANCED = "advanced"
    VECTOR = "vector"
    HYBRID = "hybrid"
    UNIVERSAL = "universal"


class TypeElementProcedure(Enum):
    """Types d'éléments de procédure"""
    ASSIGNATION = "assignation"
    CITATION = "citation"
    CONCLUSIONS = "conclusions"
    REQUETE = "requete"
    ORDONNANCE = "ordonnance"
    JUGEMENT = "jugement"
    ARRET = "arret"
    SIGNIFICATION = "signification"
    MISE_EN_DEMEURE = "mise_en_demeure"
    PROCES_VERBAL = "proces_verbal"
    EXPERTISE = "expertise"
    AUDITION = "audition"
    CONSTAT = "constat"
    NOTIFICATION = "notification"
    APPEL = "appel"
    POURVOI = "pourvoi"
    MEMOIRE = "memoire"
    DIRE = "dire"
    NOTE_PLAIDOIRIE = "note_plaidoirie"


class NaturePiece(Enum):
    """Nature des pièces versées"""
    ORIGINAL = "original"
    COPIE = "copie"
    COPIE_CERTIFIEE = "copie_certifiée_conforme"
    EXTRAIT = "extrait"
    TRADUCTION = "traduction"
    TRANSCRIPTION = "transcription"
    PHOTOGRAPHIE = "photographie"
    ENREGISTREMENT = "enregistrement"
    PLAN = "plan"
    SCHEMA = "schema"


class ForceProbante(Enum):
    """Force probante d'une pièce"""
    FAIBLE = "faible"
    NORMALE = "normale"
    FORTE = "forte"
    IRREFRAGABLE = "irréfragable"


class StyleRedaction(Enum):
    """Styles de rédaction juridique"""
    FORMEL = "formel"
    PERSUASIF = "persuasif"
    TECHNIQUE = "technique"
    SYNTHETIQUE = "synthétique"
    PEDAGOGIQUE = "pédagogique"
    PERSONNALISE = "personnalisé"


class TypeAnalyse(Enum):
    """Types d'analyse juridique"""
    GENERAL = "general_analysis"
    RISQUES = "risk_analysis"
    CONFORMITE = "compliance"
    STRATEGIE = "strategy"
    INFRACTIONS = "infractions"


class TypePartie(Enum):
    """Types de parties dans une affaire"""
    DEMANDEUR = "demandeur"
    DEFENDEUR = "défendeur"
    PLAIGNANT = "plaignant"
    MIS_EN_CAUSE = "mis_en_cause"
    TEMOIN = "témoin"
    EXPERT = "expert"
    TIERS = "tiers"
    PARTIE_CIVILE = "partie_civile"
    PREVENU = "prévenu"
    ACCUSE = "accusé"
    INTERVENANT = "intervenant"


__all__ = [
    "RiskLevel",
    "SourceJurisprudence",
    "SourceEntreprise",
    "TypeJuridiction",
    "StatutProcedural",
    "PhaseProcedure",
    "SearchMode",
    "TypeElementProcedure",
    "NaturePiece",
    "ForceProbante",
    "StyleRedaction",
    "TypeAnalyse",
    "TypePartie",
]
