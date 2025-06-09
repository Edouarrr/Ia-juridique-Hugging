# models/configurations.py
"""Configurations et constantes pour l'application juridique"""

from models.dataclasses import (
    StyleConfig, 
    StyleRedaction,
    DocumentTemplate,
    TypeDocument,
    LetterheadTemplate
)

# ========== CONFIGURATIONS DE STYLES ==========

DEFAULT_STYLE_CONFIGS = {
    StyleRedaction.FORMEL: StyleConfig(
        name="Formel",
        description="Style juridique classique et solennel",
        tone="respectueux et distant",
        vocabulary="technique et précis",
        sentence_structure="complexe",
        formality_level=9,
        typical_phrases=[
            "Il convient de relever que",
            "Aux termes de",
            "En l'espèce",
            "Il résulte de ce qui précède",
            "Force est de constater"
        ],
        argumentation_structure=[
            "Rappel des faits",
            "Analyse juridique",
            "Application au cas d'espèce",
            "Conclusion"
        ]
    ),
    StyleRedaction.PERSUASIF: StyleConfig(
        name="Persuasif",
        description="Style argumentatif et convaincant",
        tone="assertif et engagé",
        vocabulary="percutant et imagé",
        sentence_structure="variée",
        formality_level=7,
        typical_phrases=[
            "Il est manifeste que",
            "On ne saurait ignorer",
            "Il apparaît clairement",
            "La démonstration s'impose"
        ],
        argumentation_structure=[
            "Accroche forte",
            "Arguments principaux",
            "Réfutation des objections",
            "Appel à l'action"
        ]
    ),
    StyleRedaction.TECHNIQUE: StyleConfig(
        name="Technique",
        description="Style factuel et détaillé",
        tone="neutre et objectif",
        vocabulary="spécialisé et exhaustif",
        sentence_structure="structurée",
        formality_level=8,
        typical_phrases=[
            "L'analyse démontre",
            "Les éléments techniques établissent",
            "Au regard des normes applicables",
            "Conformément aux dispositions"
        ]
    ),
    StyleRedaction.SYNTHETIQUE: StyleConfig(
        name="Synthétique",
        description="Style concis et efficace",
        tone="direct et clair",
        vocabulary="simple et précis",
        sentence_structure="courte",
        formality_level=6,
        typical_phrases=[
            "En résumé",
            "Les points clés sont",
            "En substance",
            "L'essentiel réside dans"
        ]
    ),
    StyleRedaction.PEDAGOGIQUE: StyleConfig(
        name="Pédagogique",
        description="Style explicatif et accessible",
        tone="bienveillant et didactique",
        vocabulary="vulgarisé et illustré",
        sentence_structure="simple",
        formality_level=5,
        typical_phrases=[
            "Pour bien comprendre",
            "Prenons l'exemple de",
            "Concrètement",
            "En d'autres termes"
        ]
    ),
    StyleRedaction.PERSONNALISE: StyleConfig(
        name="Personnalisé",
        description="Style appris depuis vos documents",
        tone="adapté à votre pratique",
        vocabulary="votre vocabulaire habituel",
        sentence_structure="selon vos habitudes",
        formality_level=7
    )
}

# ========== TEMPLATES DE DOCUMENTS PRÉDÉFINIS ==========

BUILTIN_DOCUMENT_TEMPLATES = [
    DocumentTemplate(
        id="conclusions_defense",
        name="Conclusions en défense",
        type=TypeDocument.CONCLUSIONS,
        structure=[
            "I. FAITS ET PROCÉDURE",
            "II. DISCUSSION",
            " A. Sur la recevabilité",
            " B. Sur le fond",
            " 1. Sur l'élément matériel",
            " 2. Sur l'élément intentionnel",
            " 3. Sur le préjudice",
            "III. PAR CES MOTIFS"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure civile",
        description="Modèle de conclusions en défense pour procédure civile",
        required_fields=["partie_adverse", "juridiction", "numero_affaire"],
        optional_fields=["date_audience", "avocat_adverse"]
    ),
    DocumentTemplate(
        id="plainte_simple",
        name="Plainte simple",
        type=TypeDocument.PLAINTE,
        structure=[
            "Objet : Plainte",
            "EXPOSÉ DES FAITS",
            "QUALIFICATION JURIDIQUE",
            "PRÉJUDICES SUBIS",
            "DEMANDES",
            "PIÈCES JOINTES"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure pénale",
        description="Modèle de plainte simple au Procureur",
        required_fields=["plaignant", "mis_en_cause", "faits"],
        optional_fields=["temoins", "prejudice_montant"]
    ),
    DocumentTemplate(
        id="plainte_avec_cpc",
        name="Plainte avec constitution de partie civile",
        type=TypeDocument.PLAINTE_CPC,
        structure=[
            "Objet : Plainte avec constitution de partie civile",
            "EXPOSÉ DES FAITS",
            "QUALIFICATION JURIDIQUE",
            "PRÉJUDICES SUBIS",
            "CONSTITUTION DE PARTIE CIVILE",
            "ÉVALUATION DU PRÉJUDICE",
            "DEMANDES",
            "PIÈCES JOINTES"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure pénale",
        description="Modèle de plainte avec CPC devant le Doyen des juges d'instruction",
        required_fields=["plaignant", "mis_en_cause", "faits", "prejudice"],
        optional_fields=["consignation", "avocat"]
    ),
    DocumentTemplate(
        id="mise_en_demeure",
        name="Mise en demeure",
        type=TypeDocument.MISE_EN_DEMEURE,
        structure=[
            "MISE EN DEMEURE",
            "Rappel des faits",
            "Obligations non respectées",
            "Délai accordé",
            "Conséquences du défaut",
            "Réserves"
        ],
        style=StyleRedaction.PERSUASIF,
        category="Pré-contentieux",
        description="Modèle de mise en demeure avant action judiciaire",
        required_fields=["destinataire", "obligation", "delai"],
        optional_fields=["montant", "penalites"]
    ),
    DocumentTemplate(
        id="assignation",
        name="Assignation",
        type=TypeDocument.ASSIGNATION,
        structure=[
            "ASSIGNATION DEVANT LE [JURIDICTION]",
            "L'AN [ANNÉE] ET LE [DATE]",
            "NOUS, [HUISSIER]",
            "DONNONS ASSIGNATION À:",
            "D'AVOIR À COMPARAÎTRE",
            "FAITS ET PROCÉDURE",
            "DISCUSSION",
            "DEMANDES",
            "BORDEREAU DE PIÈCES"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure civile",
        description="Modèle d'assignation en justice",
        required_fields=["demandeur", "defendeur", "juridiction", "date_audience"],
        optional_fields=["huissier", "avocat_postulant"]
    ),
    DocumentTemplate(
        id="courrier_avocat",
        name="Courrier d'avocat",
        type=TypeDocument.COURRIER,
        structure=[
            "[EN-TÊTE CABINET]",
            "[DESTINATAIRE]",
            "[LIEU], le [DATE]",
            "Objet: [OBJET]",
            "Référence: [RÉFÉRENCE]",
            "[FORMULE D'APPEL]",
            "[CORPS DU COURRIER]",
            "[FORMULE DE POLITESSE]",
            "[SIGNATURE]"
        ],
        style=StyleRedaction.FORMEL,
        category="Correspondance",
        description="Modèle de courrier professionnel d'avocat",
        required_fields=["destinataire", "objet"],
        optional_fields=["reference", "pieces_jointes"]
    )
]

# ========== PAPIERS EN-TÊTE PRÉDÉFINIS ==========

DEFAULT_LETTERHEADS = [
    LetterheadTemplate(
        name="Cabinet standard",
        header_content="""[NOM DU CABINET]
Avocats à la Cour
[ADRESSE]
[TÉLÉPHONE] - [EMAIL]""",
        footer_content="[NOM DU CABINET] - Barreau de [VILLE] - SIRET: [NUMÉRO]",
        header_style={
            'text-align': 'center',
            'font-weight': 'bold',
            'font-size': '14px',
            'margin-bottom': '30px'
        },
        footer_style={
            'text-align': 'center',
            'font-size': '10px',
            'margin-top': '30px',
            'border-top': '1px solid #000'
        }
    ),
    LetterheadTemplate(
        name="Cabinet moderne",
        header_content="""[LOGO]
[NOM DU CABINET]
[BASELINE]""",
        footer_content="""[ADRESSE] | [TÉLÉPHONE] | [EMAIL]
[MENTIONS LÉGALES]""",
        header_style={
            'text-align': 'left',
            'font-weight': 'normal',
            'font-size': '12px',
            'margin-bottom': '40px'
        },
        footer_style={
            'text-align': 'center',
            'font-size': '9px',
            'margin-top': '40px',
            'color': '#666'
        },
        font_family="Helvetica",
        line_spacing=1.15
    ),
    LetterheadTemplate(
        name="Cabinet classique",
        header_content="""Maître [NOM]
Avocat au Barreau de [VILLE]
[SPÉCIALITÉS]

[ADRESSE LIGNE 1]
[ADRESSE LIGNE 2]
Tél: [TÉLÉPHONE]
Fax: [FAX]
Email: [EMAIL]""",
        footer_content="",
        header_style={
            'text-align': 'right',
            'font-weight': 'normal',
            'font-size': '11px',
            'margin-bottom': '50px',
            'line-height': '1.4'
        },
        page_margins={
            'top': 3.0,
            'bottom': 2.0,
            'left': 2.5,
            'right': 2.5
        }
    )
]

# ========== FORMULES JURIDIQUES ==========

FORMULES_JURIDIQUES = {
    'salutations': {
        'procureur': "Monsieur le Procureur de la République",
        'doyen': "Monsieur le Doyen des Juges d'Instruction",
        'president': "Monsieur le Président",
        'juge': "Monsieur le Juge",
        'confrere': "Mon cher Confrère",
        'client': "Madame, Monsieur"
    },
    'formules_politesse': {
        'magistrat': "Je vous prie d'agréer, Monsieur le [TITRE], l'expression de ma considération distinguée",
        'confrere': "Je vous prie de croire, mon cher Confrère, à l'assurance de mes sentiments dévoués",
        'client': "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées",
        'administration': "Je vous prie d'agréer, Madame, Monsieur, l'expression de ma considération distinguée"
    },
    'introductions': {
        'plainte': "J'ai l'honneur de porter plainte",
        'conclusions': "Pour le compte de mon client",
        'mise_demeure': "Je suis mandaté par mon client pour",
        'courrier': "Je me permets de revenir vers vous concernant"
    }
}

# ========== PATTERNS D'ARGUMENTATION ==========

ARGUMENTATION_PATTERNS = {
    'standard': [
        "En fait",
        "En droit",
        "Application au cas d'espèce",
        "Par ces motifs"
    ],
    'analytique': [
        "Rappel des faits",
        "Identification des problèmes juridiques",
        "Analyse de chaque problème",
        "Synthèse et conclusion"
    ],
    'persuasif': [
        "Contexte et enjeux",
        "Arguments principaux",
        "Réfutation des arguments adverses",
        "Conclusion et demandes"
    ],
    'chronologique': [
        "Antécédents",
        "Déroulement des faits",
        "Situation actuelle",
        "Perspectives et demandes"
    ]
}

# ========== CONFIGURATION D'ANALYSE ==========

ANALYSIS_CONFIGS = {
    'risk_analysis': {
        'focus_areas': [
            'Risques juridiques identifiés',
            'Probabilité de survenance',
            'Impact potentiel',
            'Mesures de mitigation',
            'Recommandations'
        ],
        'risk_levels': ['Faible', 'Modéré', 'Élevé', 'Critique'],
        'confidence_threshold': 0.7
    },
    'compliance': {
        'check_points': [
            'Conformité réglementaire',
            'Respect des procédures',
            'Documentation requise',
            'Délais légaux',
            'Sanctions encourues'
        ],
        'status': ['Conforme', 'Non conforme', 'À vérifier', 'Partiel']
    },
    'strategy': {
        'elements': [
            'Objectifs du client',
            'Options stratégiques',
            'Avantages/Inconvénients',
            'Recommandation',
            'Plan d'action'
        ],
        'criteria': ['Coût', 'Durée', 'Chances de succès', 'Risques']
    }
}

# ========== EXPORTS ==========

__all__ = [
    'DEFAULT_STYLE_CONFIGS',
    'BUILTIN_DOCUMENT_TEMPLATES',
    'DEFAULT_LETTERHEADS',
    'FORMULES_JURIDIQUES',
    'ARGUMENTATION_PATTERNS',
    'ANALYSIS_CONFIGS'
]