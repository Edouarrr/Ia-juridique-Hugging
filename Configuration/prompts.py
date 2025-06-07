# config/prompts.py
"""Prompts spécialisés pour l'analyse juridique"""

PROMPTS = {
    "analyse_generale": """Tu es un expert en droit pénal des affaires français. 
Analyse le cas suivant en détail :

{description_cas}

Fournis une analyse complète incluant :
1. Qualification juridique des faits
2. Infractions potentielles identifiées
3. Éléments constitutifs de chaque infraction
4. Régime de responsabilité applicable
5. Sanctions encourues
6. Jurisprudences pertinentes (avec références précises)
7. Recommandations stratégiques

Format ta réponse de manière structurée et cite toutes les sources juridiques.""",

    "abus_de_biens_sociaux": """En tant qu'expert en droit pénal des affaires, analyse ce cas d'abus de biens sociaux.

Contexte : {description_cas}

Examine spécifiquement :
1. Usage contraire à l'intérêt social
2. Usage à des fins personnelles
3. Mauvaise foi du dirigeant
4. Préjudice pour la société
5. Jurisprudences de la Chambre criminelle (citer : Cass. crim., date, n° pourvoi)

Articles de référence : L. 241-3 et L. 242-6 du Code de commerce""",

    "corruption": """Analyse ce cas potentiel de corruption en droit pénal des affaires.

Faits : {description_cas}

Vérifie la présence des éléments suivants :
1. Pacte de corruption (accord préalable)
2. Sollicitation ou agrément
3. Contrepartie (avantage indu)
4. Acte de la fonction
5. Antériorité du pacte
6. Distinction corruption active/passive

Cite les jurisprudences récentes de la Cour de cassation.
Articles : 432-11, 433-1, 435-1 et suivants du Code pénal""",

    "blanchiment": """Expertise requise sur ce cas de blanchiment présumé.

Situation : {description_cas}

Analyse :
1. Origine frauduleuse des fonds
2. Opérations de dissimulation/conversion
3. Élément intentionnel
4. Techniques utilisées
5. Présomptions légales applicables
6. Obligations de déclaration TRACFIN

Jurisprudences clés et articles 324-1 et suivants du Code pénal""",

    "delit_initie": """Analyse approfondie de ce possible délit d'initié.

Contexte : {description_cas}

Points d'analyse :
1. Information privilégiée (précise, non publique, impact sur cours)
2. Qualité d'initié (primaire/secondaire)
3. Utilisation de l'information
4. Opérations réalisées
5. Avantage indu
6. Jurisprudences AMF et Cour de cassation

Référence : L. 465-1 du Code monétaire et financier
Règlement MAR (UE) n° 596/2014""",

    "escroquerie": """Examine ce cas d'escroquerie en droit des affaires.

Éléments factuels : {description_cas}

Structure ton analyse autour :
1. Manœuvres frauduleuses caractérisées
2. Tromperie (faux nom, fausse qualité, abus de qualité vraie)
3. Remise de fonds/valeurs/biens
4. Préjudice patrimonial
5. Intention frauduleuse
6. Jurisprudences pertinentes avec numéros exacts

Article 313-1 du Code pénal et jurisprudences associées""",

    "recherche_jurisprudence": """Recherche les jurisprudences pertinentes pour cette affaire.

Contexte : {description_cas}
Type d'infraction : {type_infraction}

Fournis :
1. Jurisprudences de principe (Cass. crim. avec dates et numéros)
2. Décisions récentes (moins de 5 ans)
3. Évolutions jurisprudentielles
4. Décisions de cours d'appel pertinentes
5. Positions de la doctrine

Format : Juridiction, date, n° pourvoi, principe retenu""",

    "strategie_defense": """Élabore une stratégie de défense pour cette affaire.

Cas : {description_cas}
Infractions reprochées : {infractions}

Développe :
1. Moyens de défense au fond
2. Moyens de procédure
3. Contestation des éléments constitutifs
4. Arguments de droit
5. Jurisprudences favorables
6. Stratégie procédurale
7. Négociation éventuelle (CRPC, CJIP)""",

    "veille_juridique": """Effectue une veille juridique sur ce sujet.

Thème : {sujet}
Période : {periode}

Identifie :
1. Nouvelles législations
2. Jurisprudences récentes
3. Positions doctrinales
4. Projets de réforme
5. Actualités judiciaires
6. Tendances jurisprudentielles""",

    "verification_jurisprudence": """Vérifie l'exactitude de ces références jurisprudentielles :

{references}

Pour chaque référence, confirme :
1. Existence de la décision
2. Exactitude de la date et du numéro
3. Principe réellement énoncé
4. Portée actuelle (non remise en cause)
5. Pertinence pour le cas présent"""
}

def get_prompt(prompt_type: str, **kwargs) -> str:
    """Retourne un prompt formaté avec les paramètres fournis"""
    if prompt_type not in PROMPTS:
        raise ValueError(f"Type de prompt inconnu : {prompt_type}")
    
    return PROMPTS[prompt_type].format(**kwargs)