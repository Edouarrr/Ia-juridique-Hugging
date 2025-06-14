# managers/dynamic_generators.py
"""Générateurs dynamiques pour créer des templates et contenus à la volée"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from config.app_config import DOCUMENT_TEMPLATES, LEGAL_PHRASES, DocumentType
from modules.dataclasses import DocumentTemplate, StyleRedaction


def generate_dynamic_templates(document_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère dynamiquement des templates basés sur le contexte
    """
    # Template de base
    base_template = DOCUMENT_TEMPLATES.get(document_type, {
        "structure": ["INTRODUCTION", "DÉVELOPPEMENT", "CONCLUSION"],
        "required_sections": ["INTRODUCTION", "CONCLUSION"]
    })
    
    # Adapter selon le contexte
    if document_type == "conclusions":
        return _generate_conclusions_template(context)
    elif document_type == "assignation":
        return _generate_assignation_template(context)
    elif document_type == "plaidoirie":
        return _generate_plaidoirie_template(context)
    else:
        return _adapt_generic_template(base_template, context)

def _generate_conclusions_template(context: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un template de conclusions adapté au contexte"""
    
    # Structure de base
    structure = [
        "EN-TÊTE",
        "POUR",
        "RAPPEL DE LA PROCÉDURE",
        "RAPPEL DES FAITS"
    ]
    
    # Ajouter des sections selon le contexte
    if context.get('has_expertise', False):
        structure.append("SUR L'EXPERTISE")
    
    if context.get('infractions_count', 0) > 0:
        structure.append("SUR LA QUALIFICATION DES FAITS")
    
    # Discussion principale
    structure.append("DISCUSSION")
    
    # Sous-sections de discussion
    if context.get('responsability_claim', False):
        structure.append("  A. Sur la responsabilité")
    
    if context.get('damages_claim', False):
        structure.append("  B. Sur les préjudices")
        structure.append("  C. Sur l'évaluation des dommages-intérêts")
    
    # Sections finales
    if context.get('procedural_issues', False):
        structure.append("SUR LA PROCÉDURE")
    
    structure.extend([
        "SUR LES DEMANDES ACCESSOIRES",
        "PAR CES MOTIFS",
        "BORDEREAU DE PIÈCES"
    ])
    
    return {
        "structure": structure,
        "required_sections": ["POUR", "DISCUSSION", "PAR CES MOTIFS"],
        "variables": {
            "demandeur": context.get('demandeur', '[DEMANDEUR]'),
            "defendeur": context.get('defendeur', '[DÉFENDEUR]'),
            "tribunal": context.get('tribunal', 'Tribunal Judiciaire'),
            "numero_rg": context.get('numero_rg', '[N° RG]')
        },
        "suggested_length": {
            "RAPPEL DES FAITS": "2-3 pages",
            "DISCUSSION": "5-10 pages",
            "PAR CES MOTIFS": "1-2 pages"
        }
    }

def _generate_assignation_template(context: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un template d'assignation adapté"""
    
    structure = [
        "L'AN DEUX MILLE VINGT-CINQ",
        "À LA REQUÊTE DE",
        "AYANT POUR AVOCAT",
        "J'AI HUISSIER SOUSSIGNÉ",
        "DONNÉ ASSIGNATION À"
    ]
    
    # Adapter selon le type de procédure
    procedure_type = context.get('procedure_type', 'standard')
    
    if procedure_type == 'référé':
        structure.extend([
            "AVERTISSEMENT - PROCÉDURE DE RÉFÉRÉ",
            "TRÈS IMPORTANT"
        ])
    
    structure.extend([
        "EXPOSÉ DES FAITS ET DE LA PROCÉDURE",
        "DISCUSSION"
    ])
    
    # Ajouter les moyens selon le contexte
    if context.get('nullity_claims', False):
        structure.append("I. SUR LA NULLITÉ")
    
    if context.get('competence_issue', False):
        structure.append("II. SUR LA COMPÉTENCE")
    
    structure.extend([
        "III. SUR LE FOND",
        "IV. SUR LES DEMANDES",
        "PAR CES MOTIFS",
        "PIÈCES COMMUNIQUÉES"
    ])
    
    return {
        "structure": structure,
        "required_sections": [
            "À LA REQUÊTE DE",
            "DONNÉ ASSIGNATION À",
            "PAR CES MOTIFS"
        ],
        "variables": _get_assignation_variables(context),
        "formules_type": _get_assignation_formules(procedure_type)
    }

def _generate_plaidoirie_template(context: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un template de plaidoirie"""
    
    duration = context.get('duration_minutes', 30)
    
    # Structure adaptée à la durée
    if duration <= 15:
        structure = [
            "INTRODUCTION (2 min)",
            "FAITS ESSENTIELS (3 min)",
            "ARGUMENT PRINCIPAL (8 min)",
            "CONCLUSION (2 min)"
        ]
    elif duration <= 30:
        structure = [
            "INTRODUCTION (3 min)",
            "RAPPEL DES FAITS (5 min)",
            "PREMIER ARGUMENT (8 min)",
            "DEUXIÈME ARGUMENT (8 min)",
            "RÉFUTATION (4 min)",
            "CONCLUSION (2 min)"
        ]
    else:
        structure = [
            "INTRODUCTION (5 min)",
            "CONTEXTE ET PROCÉDURE (5 min)",
            "RAPPEL DES FAITS (8 min)",
            "PREMIER ARGUMENT (10 min)",
            "DEUXIÈME ARGUMENT (10 min)",
            "TROISIÈME ARGUMENT (8 min)",
            "RÉFUTATION DES ARGUMENTS ADVERSES (8 min)",
            "SYNTHÈSE (4 min)",
            "CONCLUSION (2 min)"
        ]
    
    return {
        "structure": structure,
        "required_sections": ["INTRODUCTION", "CONCLUSION"],
        "timing_notes": True,
        "oral_markers": [
            "[PAUSE]",
            "[INSISTER]",
            "[REGARDER LE TRIBUNAL]",
            "[MONTRER LA PIÈCE]"
        ],
        "rhetorical_devices": [
            "Questions rhétoriques",
            "Anaphores",
            "Gradations",
            "Antithèses"
        ]
    }

def _adapt_generic_template(base_template: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Adapte un template générique selon le contexte"""
    
    template = base_template.copy()
    
    # Ajouter des sections si nécessaire
    if context.get('complex_case', False):
        if "ANALYSE DÉTAILLÉE" not in template["structure"]:
            idx = template["structure"].index("DÉVELOPPEMENT") + 1
            template["structure"].insert(idx, "ANALYSE DÉTAILLÉE")
    
    # Ajouter des variables contextuelles
    template["variables"] = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "auteur": context.get('auteur', '[AUTEUR]'),
        **context.get('custom_variables', {})
    }
    
    return template

def _get_assignation_variables(context: Dict[str, Any]) -> Dict[str, str]:
    """Retourne les variables pour une assignation"""
    
    return {
        "demandeur_nom": context.get('demandeur_nom', '[NOM DEMANDEUR]'),
        "demandeur_adresse": context.get('demandeur_adresse', '[ADRESSE DEMANDEUR]'),
        "defendeur_nom": context.get('defendeur_nom', '[NOM DÉFENDEUR]'),
        "defendeur_adresse": context.get('defendeur_adresse', '[ADRESSE DÉFENDEUR]'),
        "tribunal": context.get('tribunal', 'Tribunal Judiciaire'),
        "date_audience": context.get('date_audience', '[DATE AUDIENCE]'),
        "heure_audience": context.get('heure_audience', '[HEURE]'),
        "huissier_nom": context.get('huissier_nom', '[NOM HUISSIER]'),
        "avocat_nom": context.get('avocat_nom', '[NOM AVOCAT]'),
        "avocat_barreau": context.get('avocat_barreau', '[BARREAU]')
    }

def _get_assignation_formules(procedure_type: str) -> Dict[str, List[str]]:
    """Retourne les formules types pour une assignation"""
    
    formules = {
        "standard": [
            "J'ai, Huissier de Justice soussigné",
            "Donné assignation à",
            "À comparaître devant",
            "Pour s'entendre",
            "Sous toutes réserves"
        ],
        "référé": [
            "J'ai, Huissier de Justice soussigné",
            "Donné assignation À COMPARAÎTRE D'HEURE À HEURE",
            "Devant Monsieur le Président",
            "Statuant en référé",
            "Pour s'entendre",
            "Dire et juger",
            "Le tout sous toutes réserves"
        ]
    }
    
    return formules.get(procedure_type, formules["standard"])

def generate_document_outline(document_type: str, key_points: List[str]) -> List[Dict[str, Any]]:
    """Génère un plan détaillé pour un document"""
    
    outline = []
    
    # Générer le plan selon le type
    if document_type == "conclusions":
        outline = _generate_conclusions_outline(key_points)
    elif document_type == "memoire":
        outline = _generate_memoire_outline(key_points)
    else:
        outline = _generate_generic_outline(document_type, key_points)
    
    return outline

def _generate_conclusions_outline(key_points: List[str]) -> List[Dict[str, Any]]:
    """Génère un plan détaillé pour des conclusions"""
    
    outline = [
        {
            "section": "POUR",
            "level": 1,
            "content": "Identification complète du demandeur",
            "subsections": []
        },
        {
            "section": "RAPPEL DES FAITS",
            "level": 1,
            "content": "Exposé chronologique et objectif",
            "subsections": [
                {"title": "Contexte", "points": []},
                {"title": "Événements", "points": key_points[:2] if len(key_points) > 2 else key_points}
            ]
        },
        {
            "section": "DISCUSSION",
            "level": 1,
            "content": "Analyse juridique approfondie",
            "subsections": []
        }
    ]
    
    # Ajouter les points clés dans la discussion
    for i, point in enumerate(key_points[2:] if len(key_points) > 2 else [], 1):
        outline[2]["subsections"].append({
            "title": f"Moyen {i}",
            "points": [point]
        })
    
    outline.append({
        "section": "PAR CES MOTIFS",
        "level": 1,
        "content": "Demandes au tribunal",
        "subsections": []
    })
    
    return outline

def _generate_memoire_outline(key_points: List[str]) -> List[Dict[str, Any]]:
    """Génère un plan pour un mémoire"""
    
    outline = [
        {
            "section": "INTRODUCTION",
            "level": 1,
            "content": "Présentation de la problématique",
            "subsections": []
        }
    ]
    
    # Structurer les points en parties
    if len(key_points) <= 3:
        # Une seule partie
        outline.append({
            "section": "DÉVELOPPEMENT",
            "level": 1,
            "content": "Analyse complète",
            "subsections": [{"title": p, "points": []} for p in key_points]
        })
    else:
        # Deux parties
        mid = len(key_points) // 2
        outline.extend([
            {
                "section": "PREMIÈRE PARTIE",
                "level": 1,
                "content": "Premier aspect",
                "subsections": [{"title": p, "points": []} for p in key_points[:mid]]
            },
            {
                "section": "DEUXIÈME PARTIE",
                "level": 1,
                "content": "Second aspect",
                "subsections": [{"title": p, "points": []} for p in key_points[mid:]]
            }
        ])
    
    outline.append({
        "section": "CONCLUSION",
        "level": 1,
        "content": "Synthèse et perspectives",
        "subsections": []
    })
    
    return outline

def _generate_generic_outline(document_type: str, key_points: List[str]) -> List[Dict[str, Any]]:
    """Génère un plan générique"""
    
    outline = [
        {
            "section": "INTRODUCTION",
            "level": 1,
            "content": "Présentation du sujet",
            "subsections": []
        }
    ]
    
    # Ajouter les points comme sections
    for i, point in enumerate(key_points, 1):
        outline.append({
            "section": f"PARTIE {i}",
            "level": 1,
            "content": point,
            "subsections": []
        })
    
    outline.append({
        "section": "CONCLUSION",
        "level": 1,
        "content": "Synthèse",
        "subsections": []
    })
    
    return outline