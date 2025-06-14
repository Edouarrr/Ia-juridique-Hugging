"""Configuration complète du cahier des charges pour la génération d'actes juridiques"""

from datetime import datetime
from typing import Any, Dict, List

# ========================= CONFIGURATION GÉNÉRALE =========================

CABINET_INFO = {
    "nom": "Cabinet [NOM]",
    "avocat_principal": "Me Edouard Steru",
    "barreau": "Paris",
    "adresse": "[ADRESSE CABINET]",
    "telephone": "[TÉLÉPHONE]",
    "email": "[EMAIL]",
    "toque": "[NUMÉRO TOQUE]"
}

# ========================= STYLES ET MISE EN FORME =========================

STYLE_DOCUMENT = {
    "police": {
        "famille": "Garamond",
        "taille_corps": 12,
        "taille_titre_principal": 14,
        "taille_sous_titre": 12
    },
    "marges": {
        "haut": 2.5,
        "bas": 2.5,
        "gauche": 2.5,
        "droite": 2.5
    },
    "interligne": 1.5,
    "pagination": {
        "active": True,
        "position": "bas_droite",
        "debut": 2  # Commence à la page 2
    }
}

# Hiérarchie de numérotation
HIERARCHIE_NUMEROTATION = {
    1: {
        "format": "roman_majuscule",  # I, II, III
        "style": ["gras", "souligné"],
        "police_taille": 14
    },
    2: {
        "format": "lettre_majuscule",  # A, B, C
        "style": ["gras", "souligné"],
        "police_taille": 12
    },
    3: {
        "format": "chiffre_arabe",  # 1, 2, 3
        "style": ["gras"],
        "police_taille": 12
    },
    4: {
        "format": "lettre_minuscule",  # a, b, c
        "style": ["italique"],
        "police_taille": 12
    },
    5: {
        "format": "chiffre_romain_parentheses",  # (i), (ii), (iii)
        "style": ["italique"],
        "police_taille": 12
    }
}

# ========================= STRUCTURES DES ACTES =========================

STRUCTURES_ACTES = {
    "conclusions_nullite": {
        "sections": [
            "en_tete",
            "in_limine_litis",
            "nullite_copj",
            "application_espece",
            "grief",
            "dispositif"
        ],
        "longueur_cible": 3000,
        "style": "technique"
    },
    "observations_175": {
        "sections": [
            "en_tete",
            "evolution_accusations",
            "accusations_initiales",
            "evolution_procedure",
            "demandes_non_lieu",
            "dispositif"
        ],
        "longueur_cible": 4000,
        "style": "argumentatif"
    },
    "conclusions_fond": {
        "sections": [
            "en_tete",
            "faits_procedure",
            "discussion_par_qualification",
            "volet_civil",
            "par_ces_motifs"
        ],
        "longueur_cible": 6000,
        "style": "exhaustif"
    },
    "conclusions_appel": {
        "sections": [
            "en_tete",
            "critique_motifs_droit",
            "critique_motifs_fait",
            "reponse_adverses",
            "dispositif"
        ],
        "longueur_cible": 5000,
        "style": "critique"
    },
    "citation_directe": {
        "sections": [
            "en_tete",
            "parties",
            "faits",
            "qualification",
            "competence",
            "pieces",
            "convocation"
        ],
        "longueur_cible": 2500,
        "style": "procedural"
    },
    "plainte_simple": {
        "sections": [
            "en_tete",
            "identite_plaignant",
            "faits",
            "qualification",
            "competence",
            "prescription",
            "pieces_manquantes",
            "pieces_jointes"
        ],
        "longueur_cible": 2000,
        "style": "factuel"
    },
    "plainte_cpc": {
        "sections": [
            "en_tete",
            "identite_complete",
            "faits_detailles",
            "qualification_approfondie",
            "prejudice_demandes",
            "election_domicile",
            "consignation",
            "pieces"
        ],
        "longueur_cible": 8000,
        "style": "exhaustif"
    }
}

# ========================= TEMPLATES DE SECTIONS =========================

TEMPLATES_SECTIONS = {
    "en_tete_tribunal": """A MESDAMES ET/OU MESSIEURS LES PRÉSIDENT ET JUGES COMPOSANT 
LA {numero}ᵉ CHAMBRE CORRECTIONNELLE DU TRIBUNAL JUDICIAIRE DE {ville}

Audience du {date} à {heure}
N° Parquet : {numero_parquet}""",
    
    "en_tete_instruction": """Monsieur le Doyen des Juges d'Instruction
Tribunal Judiciaire de {ville}
{adresse}

{ville}, le {date}

N° Instruction : {numero_instruction}""",
    
    "bloc_parties": """POUR : {demandeur_nom}
       {demandeur_qualite}
       {demandeur_adresse}
       
Ayant pour avocat : Me {avocat_nom}
                   Avocat au Barreau de {barreau}
                   Toque n° {toque}
                   Tél : {telephone}
                   Email : {email}

CONTRE : {defendeur_nom}
         {defendeur_qualite}
         {defendeur_adresse}""",
    
    "in_limine_litis": """IN LIMINE LITIS

Il sera démontré que la procédure est entachée de nullité pour violation 
des dispositions de l'article {article} du Code de procédure pénale.""",
    
    "formule_plaise": """PLAISE AU TRIBUNAL"""
}

# ========================= FORMULES JURIDIQUES =========================

FORMULES_JURIDIQUES = {
    "introduction": {
        "standard": "Il sera ci-après démontré que",
        "subsidiaire": "À titre subsidiaire, il convient de relever que",
        "surabondant": "Surabondamment et en tant que de besoin",
        "principal": "À titre principal, il y a lieu de constater que"
    },
    "transition": {
        "consequence": "Il résulte de ce qui précède que",
        "addition": "Au surplus, il convient d'observer que",
        "opposition": "Cependant, force est de constater que",
        "precision": "Plus précisément, il apparaît que"
    },
    "conclusion": {
        "partielle": "Il en résulte nécessairement que",
        "generale": "En conséquence de l'ensemble de ces développements",
        "dispositif": "PAR CES MOTIFS",
        "demande": "C'est pourquoi il est demandé au Tribunal de"
    }
}

# ========================= INFRACTIONS ET QUALIFICATIONS =========================

INFRACTIONS_PENALES = {
    "abus_biens_sociaux": {
        "titre": "Abus de biens sociaux",
        "articles": ["L. 241-3 du Code de commerce", "L. 242-6 du Code de commerce"],
        "elements_constitutifs": [
            "Usage des biens ou du crédit de la société",
            "Contraire à l'intérêt social",
            "À des fins personnelles",
            "Mauvaise foi"
        ],
        "peines": "5 ans d'emprisonnement et 375 000 euros d'amende",
        "prescription": "6 ans à compter de la présentation des comptes"
    },
    "corruption": {
        "titre": "Corruption",
        "articles": ["432-11 du Code pénal", "433-1 du Code pénal"],
        "elements_constitutifs": [
            "Sollicitation ou agrément",
            "Offres, promesses, dons ou présents",
            "Pour accomplir ou s'abstenir d'accomplir un acte",
            "Pacte de corruption"
        ],
        "peines": "10 ans d'emprisonnement et 1 000 000 euros d'amende",
        "prescription": "6 ans"
    },
    "escroquerie": {
        "titre": "Escroquerie",
        "articles": ["313-1 du Code pénal"],
        "elements_constitutifs": [
            "Usage d'un faux nom ou d'une fausse qualité",
            "Abus d'une qualité vraie",
            "Emploi de manœuvres frauduleuses",
            "Remise de fonds, valeurs ou biens"
        ],
        "peines": "5 ans d'emprisonnement et 375 000 euros d'amende",
        "prescription": "6 ans"
    },
    "abus_confiance": {
        "titre": "Abus de confiance",
        "articles": ["314-1 du Code pénal"],
        "elements_constitutifs": [
            "Remise volontaire",
            "À charge de restitution ou usage déterminé",
            "Détournement",
            "Préjudice"
        ],
        "peines": "3 ans d'emprisonnement et 375 000 euros d'amende",
        "prescription": "6 ans"
    },
    "blanchiment": {
        "titre": "Blanchiment",
        "articles": ["324-1 du Code pénal"],
        "elements_constitutifs": [
            "Faciliter la justification mensongère",
            "Produit d'un crime ou délit",
            "Concours à une opération de placement",
            "Connaissance de l'origine frauduleuse"
        ],
        "peines": "5 ans d'emprisonnement et 375 000 euros d'amende",
        "prescription": "6 ans"
    }
}

# ========================= JURISPRUDENCES TYPES =========================

JURISPRUDENCES_REFERENCE = {
    "nullite_garde_vue": [
        "Cass. crim., 31 mai 2011, n° 11-81.412",
        "Cass. crim., 19 sept. 2012, n° 11-88.111",
        "Cass. crim., 4 juin 2013, n° 13-81.945"
    ],
    "abus_biens_sociaux": [
        "Cass. crim., 27 oct. 2021, n° 20-82.882",
        "Cass. crim., 8 sept. 2021, n° 20-85.145",
        "Cass. crim., 6 oct. 2021, n° 20-85.434"
    ],
    "prescription": [
        "Cass. crim., 7 nov. 2012, n° 11-82.961",
        "Cass. crim., 25 sept. 2013, n° 12-85.056",
        "Cass. crim., 20 févr. 2019, n° 18-82.399"
    ]
}

# ========================= PIÈCES TYPES =========================

PIECES_TYPES = {
    "abus_biens_sociaux": [
        "Extrait Kbis de la société",
        "Statuts de la société",
        "Procès-verbaux d'assemblées générales",
        "Comptes annuels sur la période",
        "Relevés bancaires de la société",
        "Factures litigieuses",
        "Contrats mis en cause",
        "Rapport du commissaire aux comptes"
    ],
    "corruption": [
        "Échanges de courriels",
        "Relevés téléphoniques",
        "Contrats publics concernés",
        "Documents comptables",
        "Attestations de témoins",
        "Procès-verbaux d'audition"
    ]
}

# ========================= FORMULES DE POLITESSE =========================

FORMULES_POLITESSE = {
    "magistrat": {
        "formule": "Je vous prie de croire, Monsieur le Juge, à l'expression de ma très haute considération.",
        "destinataires": ["juge", "président", "conseiller"]
    },
    "procureur": {
        "formule": "Je vous prie d'agréer, Monsieur le Procureur de la République, l'expression de ma haute considération",
        "destinataires": ["procureur", "substitut", "procureur général"]
    },
    "doyen": {
        "formule": "Je vous prie d'agréer, Monsieur le Doyen, l'expression de ma considération distinguée.",
        "destinataires": ["doyen des juges d'instruction"]
    },
    "expert": {
        "formule": "Je vous prie d'agréer, Monsieur l'Expert, l'expression de mes salutations distinguées.",
        "destinataires": ["expert judiciaire", "expert comptable"]
    },
    "confrere": {
        "formule": "Je vous prie de me croire, Votre bien dévoué Confrère",
        "destinataires": ["avocat", "confrère", "consœur"]
    },
    "greffier": {
        "formule": "Je vous prie d'agréer, Monsieur/Madame le Greffier, l'expression de mes salutations distinguées.",
        "destinataires": ["greffier", "greffier en chef"]
    }
}

# ========================= RÈGLES DE VALIDATION =========================

REGLES_VALIDATION = {
    "longueur_minimale": {
        "plainte_simple": 1500,
        "plainte_cpc": 6000,
        "conclusions": 3000,
        "conclusions_appel": 4000,
        "assignation": 2000
    },
    "elements_obligatoires": {
        "tous": ["en_tete", "parties", "dispositif", "signature"],
        "plainte": ["faits", "qualification", "prejudice"],
        "conclusions": ["in_limine_litis", "discussion", "moyens"],
        "assignation": ["convocation", "competence", "demandes"]
    },
    "pieces_minimales": {
        "plainte": 3,
        "conclusions": 5,
        "assignation": 2
    }
}

# ========================= MESSAGES D'ERREUR =========================

MESSAGES_ERREUR = {
    "parties_manquantes": "Les parties doivent être renseignées",
    "infractions_manquantes": "Au moins une infraction doit être sélectionnée",
    "longueur_insuffisante": "Le document ne respecte pas la longueur minimale requise",
    "structure_incomplete": "La structure du document est incomplète",
    "pieces_insuffisantes": "Le nombre de pièces est insuffisant"
}

# ========================= PROMPTS LLM SPÉCIALISÉS =========================

PROMPTS_GENERATION = {
    "style_instruction": """Tu es Maître Edouard Steru, avocat pénaliste au Barreau de Paris, 
spécialisé en droit pénal des affaires. Tu rédiges dans un style juridique français 
traditionnel, avec rigueur et élégance. Utilise le vouvoiement, des phrases complexes 
mais claires, et respecte scrupuleusement la hiérarchie I > A > 1 > a > i).""",
    
    "plainte_exhaustive": """Rédige une plainte avec constitution de partie civile EXHAUSTIVE.
IMPÉRATIF : Le document doit faire AU MINIMUM 8000 mots.

Structure obligatoire :
I. EXPOSÉ DÉTAILLÉ DES FAITS (3000+ mots)
   - Contexte complet de l'affaire
   - Chronologie précise avec dates
   - Description minutieuse de chaque fait
   - Montants et préjudices détaillés
   
II. DISCUSSION JURIDIQUE APPROFONDIE (3000+ mots)
    Pour CHAQUE infraction :
    A. Textes applicables (citations complètes)
    B. Éléments constitutifs détaillés
    C. Application aux faits (point par point)
    D. Jurisprudences (au moins 3 par infraction)
    E. Réfutation des arguments adverses
    
III. PRÉJUDICES (1000+ mots)
     - Financier (chiffré précisément)
     - Moral (développé)
     - Image et réputation
     
IV. DEMANDES ET CONSTITUTION (1000+ mots)

Utilise un vocabulaire juridique soutenu, des références précises, 
et anticipe tous les contre-arguments possibles.""",
    
    "conclusions_nullite": """Rédige des conclusions aux fins de nullité.
Focus sur la rigueur procédurale et la technicité juridique.
Cite systématiquement la jurisprudence de la Cour de cassation.
Structure : violation du texte → application → grief → nullité."""
}

# ========================= EXPORT DE LA CONFIGURATION =========================

def get_config_for_acte(type_acte: str) -> Dict[str, Any]:
    """Retourne la configuration complète pour un type d'acte"""
    return {
        "structure": STRUCTURES_ACTES.get(type_acte, {}),
        "templates": TEMPLATES_SECTIONS,
        "style": STYLE_DOCUMENT,
        "hierarchie": HIERARCHIE_NUMEROTATION,
        "formules": FORMULES_JURIDIQUES,
        "validation": REGLES_VALIDATION
    }

def get_infraction_details(code_infraction: str) -> Dict[str, Any]:
    """Retourne les détails complets d'une infraction"""
    return INFRACTIONS_PENALES.get(code_infraction, {})

def get_jurisprudences_for_theme(theme: str) -> List[str]:
    """Retourne les jurisprudences pertinentes pour un thème"""
    return JURISPRUDENCES_REFERENCE.get(theme, [])

def validate_acte(acte_content: str, type_acte: str) -> Dict[str, Any]:
    """Valide un acte selon les règles du cahier des charges"""
    errors = []
    warnings = []
    
    # Vérifier la longueur
    word_count = len(acte_content.split())
    min_length = REGLES_VALIDATION["longueur_minimale"].get(type_acte, 1000)
    
    if word_count < min_length:
        errors.append(f"Longueur insuffisante : {word_count} mots (minimum : {min_length})")
    
    # Vérifier les éléments obligatoires
    elements_requis = REGLES_VALIDATION["elements_obligatoires"]["tous"]
    elements_requis.extend(REGLES_VALIDATION["elements_obligatoires"].get(type_acte, []))
    
    for element in elements_requis:
        if element.upper() not in acte_content.upper():
            warnings.append(f"Élément manquant : {element}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "word_count": word_count
    }