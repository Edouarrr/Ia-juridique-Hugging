# models/configurations.py
"""Configurations pour les templates de génération de documents"""

import json
from datetime import datetime
from typing import Any, Dict, List

from config.app_config import DocumentType
from modules.dataclasses import (DocumentTemplate, LetterheadTemplate,
                                 StyleConfig, StyleRedaction)

# ========== PAPIERS EN-TÊTE PAR DÉFAUT ==========

DEFAULT_LETTERHEADS = [
    LetterheadTemplate(
        name="Cabinet classique",
        header_content="""CABINET D\'AVOCATS
[NOM DU CABINET]
[ADRESSE]
[TÉLÉPHONE] - [EMAIL]
Barreau de [VILLE]""",
        footer_content="""[NOM DU CABINET] - SELARL au capital de [CAPITAL] €
RCS [VILLE] [NUMÉRO] - TVA : [TVA] - Toque : [TOQUE]
[ADRESSE COMPLÈTE]""",
        logo_path=None,
        header_style={
            'text-align': 'center',
            'font-weight': 'bold',
            'font-size': '14px',
            'margin-bottom': '30px',
            'text-transform': 'uppercase'
        },
        footer_style={
            'text-align': 'center',
            'font-size': '9px',
            'margin-top': '40px',
            'color': '#666666'
        },
        page_margins={
            'top': 3.0,
            'bottom': 2.5,
            'left': 2.5,
            'right': 2.5
        },
        font_family="Times New Roman",
        font_size=11,
        line_spacing=1.5
    ),
    
    LetterheadTemplate(
        name="Cabinet moderne",
        header_content="""[LOGO]
[NOM ASSOCIÉ 1] | [NOM ASSOCIÉ 2] | [NOM ASSOCIÉ 3]
AVOCATS ASSOCIÉS
[ADRESSE LIGNE 1] - [ADRESSE LIGNE 2]
T. [TÉLÉPHONE] - F. [FAX] - [EMAIL] - [SITE WEB]""",
        footer_content="""[NOM CABINET] - Société d\'avocats - Barreau de [VILLE]
SIRET : [SIRET] - TVA Intracommunautaire : [TVA]""",
        logo_path=None,
        header_style={
            'text-align': 'left',
            'font-weight': 'normal',
            'font-size': '12px',
            'margin-bottom': '25px',
            'line-height': '1.4'
        },
        footer_style={
            'text-align': 'left',
            'font-size': '8px',
            'margin-top': '30px',
            'color': '#888888',
            'border-top': '1px solid #cccccc',
            'padding-top': '10px'
        },
        page_margins={
            'top': 2.5,
            'bottom': 2.0,
            'left': 3.0,
            'right': 2.5
        },
        font_family="Arial",
        font_size=11,
        line_spacing=1.5
    ),
    
    LetterheadTemplate(
        name="Cabinet minimaliste",
        header_content="""[NOM CABINET]
[EMAIL] | [TÉLÉPHONE]""",
        footer_content="""[ADRESSE] - [CODE POSTAL] [VILLE]
Barreau de [VILLE] - Toque [NUMÉRO]""",
        logo_path=None,
        header_style={
            'text-align': 'right',
            'font-weight': 'bold',
            'font-size': '16px',
            'margin-bottom': '40px',
            'color': '#333333'
        },
        footer_style={
            'text-align': 'right',
            'font-size': '9px',
            'margin-top': '50px',
            'color': '#999999'
        },
        page_margins={
            'top': 2.0,
            'bottom': 2.0,
            'left': 2.5,
            'right': 2.5
        },
        font_family="Helvetica",
        font_size=11,
        line_spacing=1.5
    ),
    
    LetterheadTemplate(
        name="Cabinet institutionnel",
        header_content="""ÉTUDE D\'AVOCATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NOM CABINET]
[SPÉCIALITÉS]

[ADRESSE LIGNE 1]
[ADRESSE LIGNE 2]
[CODE POSTAL] [VILLE]

Téléphone : [TÉLÉPHONE]
Télécopie : [FAX]
Courriel : [EMAIL]""",
        footer_content="""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Société d\'exercice libéral par actions simplifiée d\'avocats
Capital social : [CAPITAL] € - RCS [VILLE] [RCS] - Code APE : [APE]
TVA intracommunautaire : [TVA] - Barreau de [VILLE]""",
        logo_path=None,
        header_style={
            'text-align': 'center',
            'font-weight': 'normal',
            'font-size': '12px',
            'margin-bottom': '35px',
            'line-height': '1.6'
        },
        footer_style={
            'text-align': 'center',
            'font-size': '8px',
            'margin-top': '35px',
            'color': '#555555',
            'line-height': '1.4'
        },
        page_margins={
            'top': 3.5,
            'bottom': 3.0,
            'left': 2.5,
            'right': 2.5
        },
        font_family="Georgia",
        font_size=11,
        line_spacing=1.5
    ),
    
    LetterheadTemplate(
        name="Cabinet avec colonnes",
        header_content="""[LOGO]
┌─────────────────────────┬──────────────────────────────────┐
│ [NOM CABINET]           │ [ASSOCIÉ 1], Avocat associé     │
│ Avocats à la Cour       │ [ASSOCIÉ 2], Avocat associé     │
│                         │ [COLLABORATEUR 1], Avocat        │
│ [ADRESSE]               │ [COLLABORATEUR 2], Avocat        │
│ [CODE POSTAL] [VILLE]   │                                  │
│                         │ [EMAIL GÉNÉRAL]                  │
│ T : [TÉLÉPHONE]         │ [SITE WEB]                       │
│ F : [FAX]               │                                  │
└─────────────────────────┴──────────────────────────────────┘""",
        footer_content="""Palais de Justice de [VILLE] - Case [NUMÉRO]
SELARL au capital de [CAPITAL] € - RCS [VILLE] [RCS] - TVA : [TVA]""",
        logo_path=None,
        header_style={
            'text-align': 'left',
            'font-family': 'Courier New',
            'font-size': '10px',
            'margin-bottom': '30px',
            'white-space': 'pre'
        },
        footer_style={
            'text-align': 'center',
            'font-size': '8px',
            'margin-top': '40px',
            'color': '#666666'
        },
        page_margins={
            'top': 2.5,
            'bottom': 2.5,
            'left': 2.0,
            'right': 2.0
        },
        font_family="Arial",
        font_size=11,
        line_spacing=1.5
    ),
    
    LetterheadTemplate(
        name="Cabinet élégant",
        header_content="""[NOM ASSOCIÉ PRINCIPAL]
ET ASSOCIÉS
────────────────────────────────────
AVOCATS AU BARREAU DE [VILLE]

[ADRESSE PRESTIGIEUSE]
[CODE POSTAL] [VILLE] CEDEX

TÉLÉPHONE : [TÉLÉPHONE]
TÉLÉCOPIE : [FAX]
COURRIEL : [EMAIL]""",
        footer_content="""────────────────────────────────────
SCP D\'AVOCATS - PALAIS DE JUSTICE, CASE [NUMÉRO] - [CODE POSTAL] [VILLE]
RCS [VILLE] [RCS] - TVA INTRACOMMUNAUTAIRE : [TVA]""",
        logo_path=None,
        header_style={
            'text-align': 'center',
            'font-weight': 'normal',
            'font-size': '13px',
            'margin-bottom': '35px',
            'line-height': '1.8',
            'letter-spacing': '1px'
        },
        footer_style={
            'text-align': 'center',
            'font-size': '8px',
            'margin-top': '45px',
            'color': '#444444',
            'letter-spacing': '0.5px'
        },
        page_margins={
            'top': 3.5,
            'bottom': 3.0,
            'left': 3.0,
            'right': 3.0
        },
        font_family="Garamond",
        font_size=12,
        line_spacing=1.6
    ),
    
    LetterheadTemplate(
        name="Cabinet numérique",
        header_content="""[NOM CABINET] | AVOCATS 2.0
[EMAIL] - [TÉLÉPHONE] - [SITE WEB]
Visio : [LIEN VISIO] - LinkedIn : [LINKEDIN]""",
        footer_content="""Signature électronique certifiée - Coffre-fort numérique sécurisé
[ADRESSE] - SIRET : [SIRET] - Membre du réseau [RÉSEAU]""",
        logo_path=None,
        header_style={
            'text-align': 'left',
            'font-weight': 'bold',
            'font-size': '11px',
            'margin-bottom': '25px',
            'color': '#2c3e50'
        },
        footer_style={
            'text-align': 'left',
            'font-size': '8px',
            'margin-top': '30px',
            'color': '#7f8c8d'
        },
        page_margins={
            'top': 2.0,
            'bottom': 2.0,
            'left': 2.5,
            'right': 2.5
        },
        font_family="Segoe UI",
        font_size=11,
        line_spacing=1.4
    ),
    
    LetterheadTemplate(
        name="Cabinet spécialisé",
        header_content="""[NOM CABINET]
AVOCATS SPÉCIALISÉS EN [SPÉCIALITÉ]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Certificat de spécialisation n°[NUMÉRO]

[ADRESSE] - [CODE POSTAL] [VILLE]
T. [TÉLÉPHONE] - F. [FAX] - [EMAIL]""",
        footer_content="""Membre de [ASSOCIATION SPÉCIALISÉE] - Formateur [ORGANISME]
[NOM STRUCTURE] - RCS [VILLE] [RCS] - Assurance RCP [ASSUREUR] n°[POLICE]""",
        logo_path=None,
        header_style={
            'text-align': 'center',
            'font-weight': 'normal',
            'font-size': '12px',
            'margin-bottom': '30px',
            'line-height': '1.6'
        },
        footer_style={
            'text-align': 'center',
            'font-size': '8px',
            'margin-top': '35px',
            'color': '#666666'
        },
        page_margins={
            'top': 3.0,
            'bottom': 2.5,
            'left': 2.5,
            'right': 2.5
        },
        font_family="Calibri",
        font_size=11,
        line_spacing=1.5
    )
]

# ========== TEMPLATES DE DOCUMENTS INTÉGRÉS ==========

BUILTIN_DOCUMENT_TEMPLATES = [
    DocumentTemplate(
        id="plainte_simple",
        name="Plainte simple",
        type=DocumentType.PLAINTE,
        structure=[
            "Monsieur le Procureur de la République,",
            "",
            "J\'ai l\'honneur de porter plainte contre [MIS EN CAUSE] pour les faits suivants :",
            "",
            "## EXPOSÉ DES FAITS",
            "[Description détaillée des faits]",
            "",
            "## PRÉJUDICE SUBI",
            "[Description du préjudice]",
            "",
            "## DEMANDES",
            "En conséquence, je sollicite :",
            "- L\'ouverture d\'une enquête",
            "- [Autres demandes]",
            "",
            "Je me tiens à votre disposition pour tout complément d\'information.",
            "",
            "Je vous prie d\'agréer, Monsieur le Procureur de la République, l\'expression de ma haute considération.",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.FORMEL,
        category="Pénal",
        description="Modèle de plainte simple pour le Procureur de la République"
    ),
    
    DocumentTemplate(
        id="plainte_cpc",
        name="Plainte avec constitution de partie civile",
        type=DocumentType.PLAINTE_CPC,
        structure=[
            "Monsieur le Doyen des Juges d\'Instruction,",
            "",
            "J\'ai l\'honneur de déposer entre vos mains une plainte avec constitution de partie civile contre :",
            "",
            "[IDENTIFICATION DES MIS EN CAUSE]",
            "",
            "Pour les infractions suivantes :",
            "[LISTE DES INFRACTIONS]",
            "",
            "## I. EXPOSÉ DES FAITS",
            "[Chronologie détaillée des faits]",
            "",
            "## II. ÉLÉMENTS DE PREUVE",
            "[Liste des preuves et pièces]",
            "",
            "## III. QUALIFICATION JURIDIQUE",
            "[Analyse juridique des infractions]",
            "",
            "## IV. PRÉJUDICE",
            "[Détail du préjudice moral et/ou matériel]",
            "",
            "## V. CONSTITUTION DE PARTIE CIVILE",
            "Je me constitue partie civile et sollicite la condamnation des mis en cause à me verser :",
            "- Au titre du préjudice moral : [montant] euros",
            "- Au titre du préjudice matériel : [montant] euros",
            "",
            "PAR CES MOTIFS,",
            "Je vous demande de bien vouloir :",
            "- Recevoir ma plainte avec constitution de partie civile",
            "- Ordonner l\'ouverture d\'une information judiciaire",
            "- [Autres demandes]",
            "",
            "Sous toutes réserves",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.FORMEL,
        category="Pénal",
        description="Modèle de plainte avec constitution de partie civile pour saisir le juge d\'instruction"
    ),
    
    DocumentTemplate(
        id="conclusions_demandeur",
        name="Conclusions pour demandeur",
        type=DocumentType.CONCLUSIONS,
        structure=[
            "TRIBUNAL [TYPE] DE [VILLE]",
            "",
            "CONCLUSIONS",
            "",
            "POUR : [DEMANDEUR]",
            "CONTRE : [DÉFENDEUR]",
            "",
            "RG N° : [NUMÉRO]",
            "",
            "## RAPPEL DES FAITS ET DE LA PROCÉDURE",
            "",
            "1. [Rappel chronologique]",
            "",
            "## DISCUSSION",
            "",
            "### I. SUR [PREMIER MOYEN]",
            "",
            "A. En droit",
            "[Argumentation juridique]",
            "",
            "B. En fait",
            "[Application aux faits de l\'espèce]",
            "",
            "### II. SUR [DEUXIÈME MOYEN]",
            "[Structure similaire]",
            "",
            "## SUR LES DEMANDES",
            "",
            "### Demande principale",
            "[Détail et justification]",
            "",
            "### Demandes subsidiaires",
            "[Si applicable]",
            "",
            "PAR CES MOTIFS,",
            "",
            "Plaise au Tribunal de :",
            "- [Liste numérotée des demandes]",
            "",
            "Sous toutes réserves",
            "",
            "[Signature avocat]"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure civile",
        description="Modèle de conclusions pour la partie demanderesse"
    ),
    
    DocumentTemplate(
        id="assignation",
        name="Assignation devant le Tribunal",
        type=DocumentType.ASSIGNATION,
        structure=[
            "L\'AN [ANNÉE] ET LE [DATE]",
            "",
            "À LA REQUÊTE DE :",
            "[IDENTIFICATION COMPLÈTE DU DEMANDEUR]",
            "",
            "J\'AI, HUISSIER DE JUSTICE SOUSSIGNÉ,",
            "",
            "DONNÉ ASSIGNATION À :",
            "[IDENTIFICATION COMPLÈTE DU DÉFENDEUR]",
            "",
            "À COMPARAÎTRE :",
            "Le [DATE AUDIENCE] à [HEURE]",
            "Devant le [TRIBUNAL]",
            "Siégeant [ADRESSE]",
            "",
            "## EXPOSÉ DES FAITS",
            "[Narration détaillée]",
            "",
            "## DISCUSSION JURIDIQUE",
            "[Fondements juridiques]",
            "",
            "## PIÈCES",
            "Le demandeur verse aux débats les pièces suivantes :",
            "[Liste des pièces]",
            "",
            "PAR CES MOTIFS,",
            "",
            "Il est demandé au Tribunal de :",
            "[Liste des demandes]",
            "",
            "SOUS TOUTES RÉSERVES",
            "",
            "[Mentions légales obligatoires]"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure civile",
        description="Modèle d\'assignation en justice"
    ),
    
    DocumentTemplate(
        id="mise_en_demeure",
        name="Mise en demeure",
        type=DocumentType.MISE_EN_DEMEURE,
        structure=[
            "[EN-TÊTE]",
            "",
            "Lettre recommandée avec accusé de réception",
            "",
            "[Lieu], le [Date]",
            "",
            "Objet : Mise en demeure",
            "",
            "Madame, Monsieur,",
            "",
            "Par la présente, je vous mets en demeure de [OBLIGATION].",
            "",
            "En effet, [RAPPEL DES FAITS ET DU FONDEMENT].",
            "",
            "Malgré mes relances [DÉMARCHES AMIABLES], vous n\'avez pas donné suite.",
            "",
            "En conséquence, je vous demande de [ACTION PRÉCISE] dans un délai de [DÉLAI] à compter de la réception de la présente.",
            "",
            "À défaut, je me verrai contraint de saisir les tribunaux compétents pour obtenir :",
            "- [Demande principale]",
            "- [Dommages et intérêts]",
            "- [Frais de procédure]",
            "",
            "Dans l\'attente de votre réponse, je vous prie d\'agréer, Madame, Monsieur, l\'expression de mes salutations distinguées.",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.FORMEL,
        category="Courriers",
        description="Modèle de mise en demeure précontentieuse"
    ),
    
    DocumentTemplate(
        id="contrat_simple",
        name="Contrat type",
        type=DocumentType.CONTRAT,
        structure=[
            "CONTRAT DE [TYPE]",
            "",
            "ENTRE LES SOUSSIGNÉS :",
            "",
            "[PARTIE 1], ci-après dénommé « [DÉNOMINATION] »",
            "D\'une part,",
            "",
            "ET",
            "",
            "[PARTIE 2], ci-après dénommé « [DÉNOMINATION] »",
            "D\'autre part,",
            "",
            "IL A ÉTÉ CONVENU CE QUI SUIT :",
            "",
            "## Article 1 - Objet",
            "[Description de l\'objet du contrat]",
            "",
            "## Article 2 - Obligations des parties",
            "### 2.1 Obligations de [PARTIE 1]",
            "[Liste des obligations]",
            "",
            "### 2.2 Obligations de [PARTIE 2]",
            "[Liste des obligations]",
            "",
            "## Article 3 - Prix et modalités de paiement",
            "[Conditions financières]",
            "",
            "## Article 4 - Durée",
            "[Durée et conditions de renouvellement]",
            "",
            "## Article 5 - Résiliation",
            "[Conditions de résiliation]",
            "",
            "## Article 6 - Litiges",
            "Tout litige sera soumis aux tribunaux compétents de [VILLE].",
            "",
            "Fait à [LIEU], le [DATE]",
            "En [NOMBRE] exemplaires originaux",
            "",
            "[Signatures des parties]"
        ],
        style=StyleRedaction.SYNTHETIQUE,
        category="Contrats",
        description="Modèle de contrat générique"
    ),
    
    DocumentTemplate(
        id="memoire_defense",
        name="Mémoire en défense",
        type=DocumentType.MEMOIRE,
        structure=[
            "MÉMOIRE EN DÉFENSE",
            "",
            "POUR : [DÉFENDEUR]",
            "CONTRE : [DEMANDEUR]",
            "",
            "## I. RAPPEL DES FAITS ET DE LA PROCÉDURE",
            "[Présentation objective]",
            "",
            "## II. DISCUSSION",
            "",
            "### A. Sur l\'irrecevabilité des demandes",
            "[Si applicable]",
            "",
            "### B. Sur le mal-fondé des demandes",
            "",
            "#### 1. Sur [PREMIÈRE DEMANDE]",
            "[Réfutation point par point]",
            "",
            "#### 2. Sur [DEUXIÈME DEMANDE]",
            "[Réfutation point par point]",
            "",
            "### C. À titre reconventionnel",
            "[Demandes reconventionnelles si applicable]",
            "",
            "## III. SUR LES PIÈCES ADVERSES",
            "[Contestation des pièces si nécessaire]",
            "",
            "PAR CES MOTIFS,",
            "",
            "Plaise au Tribunal de :",
            "- Débouter [DEMANDEUR] de l\'ensemble de ses demandes",
            "- [Demandes reconventionnelles]",
            "- Condamner [DEMANDEUR] aux dépens",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure",
        description="Modèle de mémoire pour la défense"
    ),
    
    DocumentTemplate(
        id="requete_simple",
        name="Requête",
        type=DocumentType.REQUETE,
        structure=[
            "REQUÊTE AUX FINS DE [OBJET]",
            "",
            "À Monsieur/Madame le Président du [JURIDICTION]",
            "",
            "Le requérant a l\'honneur de vous exposer ce qui suit :",
            "",
            "## FAITS",
            "[Exposé des faits]",
            "",
            "## DISCUSSION",
            "[Fondements juridiques]",
            "",
            "## DEMANDE",
            "C\'est pourquoi le requérant sollicite qu\'il plaise au Tribunal de :",
            "[Demande précise]",
            "",
            "PIÈCES JOINTES :",
            "[Liste des pièces]",
            "",
            "[Date et signature]"
        ],
        style=StyleRedaction.FORMEL,
        category="Procédure",
        description="Modèle de requête simple"
    ),
    
    DocumentTemplate(
        id="courrier_adversaire",
        name="Courrier à confrère",
        type=DocumentType.COURRIER,
        structure=[
            "[EN-TÊTE CABINET]",
            "",
            "[Date]",
            "",
            "Maître [NOM]",
            "[Adresse]",
            "",
            "Nos réf. : [RÉFÉRENCE]",
            "Vos réf. : [RÉFÉRENCE]",
            "Affaire : [PARTIES]",
            "",
            "Cher Confrère,",
            "",
            "[Corps du courrier]",
            "",
            "Dans l\'attente de vous lire, je vous prie de croire, Cher Confrère, en l\'assurance de mes sentiments confraternels dévoués.",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.PEDAGOGIQUE,
        category="Correspondance",
        description="Modèle de courrier entre avocats"
    ),
    
    DocumentTemplate(
        id="note_analyse",
        name="Note d\'analyse juridique",
        type=DocumentType.NOTE,
        structure=[
            "NOTE D\'ANALYSE",
            "",
            "Date : [DATE]",
            "Objet : [OBJET]",
            "Référence : [RÉFÉRENCE]",
            "",
            "## RÉSUMÉ EXÉCUTIF",
            "[Points clés en 3-5 lignes]",
            "",
            "## I. CONTEXTE",
            "[Présentation du contexte]",
            "",
            "## II. ANALYSE JURIDIQUE",
            "### A. Qualification des faits",
            "[Analyse]",
            "",
            "### B. Règles applicables",
            "[Textes et jurisprudence]",
            "",
            "### C. Application au cas d\'espèce",
            "[Raisonnement]",
            "",
            "## III. ÉVALUATION DES RISQUES",
            "[Analyse des risques]",
            "",
            "## IV. RECOMMANDATIONS",
            "1. [Recommandation 1]",
            "2. [Recommandation 2]",
            "",
            "## V. PROCHAINES ÉTAPES",
            "[Plan d\'action]",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.SYNTHETIQUE,
        category="Analyse",
        description="Modèle de note d\'analyse juridique interne"
    )
]

# ========== CONFIGURATIONS DE STYLE PAR DÉFAUT ==========

DEFAULT_STYLE_CONFIGS = {
    "formel": StyleConfig(
        name="Formel traditionnel",
        formality_level="tres_formel",
        sentence_length_target=25,
        paragraph_length_target=150,
        use_numbering=True,
        numbering_style="numeric",
        common_phrases=[
            "Il convient de relever que",
            "Il résulte de ce qui précède que",
            "Force est de constater que",
            "Il apparaît que",
            "Il en découle que",
            "Au surplus",
            "En tout état de cause",
            "Attendu que",
            "Considérant que",
            "Il échet de préciser que"
        ],
        transition_words=[
            "toutefois", "cependant", "néanmoins", "par ailleurs",
            "en outre", "de plus", "ainsi", "donc", "par conséquent",
            "dès lors", "en effet", "or", "mais", "enfin",
            "d'une part", "d'autre part", "au demeurant", "partant"
        ],
        preferred_conjunctions=[
            "toutefois", "néanmoins", "cependant", "or", "partant"
        ],
        technical_terms_density="high",
        active_voice_preference=0.3,
        citation_style="detailed"
    ),
    
    "simple": StyleConfig(
        name="Style simplifié",
        formality_level="formel",
        sentence_length_target=15,
        paragraph_length_target=80,
        use_numbering=True,
        numbering_style="dash",
        common_phrases=[
            "Il faut noter que",
            "On constate que",
            "Il est établi que",
            "Les faits montrent que",
            "L'analyse révèle que"
        ],
        transition_words=[
            "de plus", "également", "ensuite", "par ailleurs",
            "cependant", "toutefois", "néanmoins", "ainsi"
        ],
        preferred_conjunctions=[
            "mais", "donc", "car", "ainsi", "cependant"
        ],
        technical_terms_density="medium",
        active_voice_preference=0.6,
        citation_style="standard"
    ),
    
    "persuasif": StyleConfig(
        name="Persuasif argumenté",
        formality_level="formel",
        sentence_length_target=20,
        paragraph_length_target=120,
        use_numbering=True,
        numbering_style="numeric",
        common_phrases=[
            "Il est manifeste que",
            "À l'évidence",
            "Sans conteste",
            "Il ne fait aucun doute que",
            "Force est d'admettre que",
            "Il est indéniable que"
        ],
        transition_words=[
            "qui plus est", "au surplus", "mieux encore",
            "à cet égard", "dans ces conditions", "partant",
            "en conséquence", "dès lors", "au demeurant"
        ],
        preferred_conjunctions=[
            "dès lors", "partant", "ainsi", "en conséquence"
        ],
        technical_terms_density="medium",
        active_voice_preference=0.5,
        citation_style="detailed"
    ),
    
    "synthetique": StyleConfig(
        name="Synthétique efficace",
        formality_level="formel",
        sentence_length_target=12,
        paragraph_length_target=60,
        use_numbering=True,
        numbering_style="bullet",
        common_phrases=[
            "En résumé",
            "Les points clés sont",
            "Il ressort que",
            "L'essentiel est"
        ],
        transition_words=[
            "ensuite", "puis", "enfin", "d'abord",
            "premièrement", "deuxièmement", "en conclusion"
        ],
        preferred_conjunctions=[
            "et", "ou", "donc", "ainsi"
        ],
        technical_terms_density="low",
        active_voice_preference=0.8,
        citation_style="minimal"
    )
}

# ========== FORMULES JURIDIQUES ==========

FORMULES_JURIDIQUES = {
    'introduction': {
        'plainte': [
            "J\'ai l\'honneur de porter plainte contre {partie} pour les faits suivants :",
            "Par la présente, je souhaite porter à votre connaissance les agissements délictueux de {partie}",
            "Je soussigné(e), {plaignant}, porte plainte pour les faits ci-après exposés",
            "Je me permets de solliciter votre intervention concernant les faits graves suivants",
            "J\'ai l\'honneur de vous saisir d\'une plainte concernant {partie}"
        ],
        'conclusions': [
            "Pour les motifs ci-après développés, le {demandeur} a l\'honneur d\'exposer ce qui suit :",
            "Il sera démontré dans les présentes conclusions que {these_principale}",
            "Les développements qui suivent établiront que {objectif}",
            "Le {demandeur} entend démontrer par les présentes que",
            "Aux termes des présentes conclusions, il sera établi que"
        ],
        'assignation': [
            "L\'an {annee} et le {date}, à la requête de {demandeur}",
            "Nous, {huissier}, huissier de justice, avons donné assignation à {defendeur}",
            "Par exploit de notre ministère, assignation est donnée à {partie}",
            "À la demande de {demandeur}, nous avons fait citation à comparaître",
            "Par acte de notre ministère, nous avons assigné {defendeur}"
        ],
        'mise_en_demeure': [
            "Par la présente, je vous mets en demeure de {obligation}",
            "Je vous somme de {action} dans les plus brefs délais",
            "Vous êtes mis en demeure de procéder à {obligation}",
            "La présente constitue une mise en demeure de {action}",
            "Sans réponse de votre part sous {delai}, je me verrai contraint de"
        ]
    },
    'transition': {
        'moreover': [
            "En outre,",
            "Par ailleurs,",
            "De surcroît,",
            "Qui plus est,",
            "Au surplus,",
            "De plus,",
            "Également,",
            "Aussi convient-il de relever que"
        ],
        'consequence': [
            "En conséquence,",
            "Par conséquent,",
            "Il s\'ensuit que",
            "Partant,",
            "Dès lors,",
            "Il en résulte que",
            "Il en découle que",
            "Ainsi,"
        ],
        'opposition': [
            "Cependant,",
            "Néanmoins,",
            "Pour autant,",
            "Toutefois,",
            "Nonobstant,",
            "En revanche,",
            "Or,",
            "Pourtant,"
        ],
        'precision': [
            "En l\'espèce,",
            "Plus précisément,",
            "À cet égard,",
            "Sur ce point,",
            "S\'agissant de",
            "Concernant",
            "Quant à",
            "Au cas présent,"
        ]
    },
    'argumentation': {
        'affirmation': [
            "Il est constant que",
            "Il est établi que",
            "Il ne fait aucun doute que",
            "Il est manifeste que",
            "Force est de constater que",
            "Il apparaît que",
            "Il résulte de ce qui précède que",
            "Il convient de relever que"
        ],
        'refutation': [
            "Contrairement à ce qui est soutenu",
            "Il ne saurait être prétendu que",
            "C\'est à tort que",
            "Il est erroné de soutenir que",
            "Cette argumentation ne résiste pas à l\'analyse",
            "Cette thèse ne peut prospérer",
            "Ce moyen est inopérant",
            "Cette prétention est mal fondée"
        ],
        'nuance': [
            "Sans qu\'il soit nécessaire de",
            "Quand bien même",
            "À supposer même que",
            "En admettant que",
            "Même à considérer que",
            "Pour autant que",
            "Dans la mesure où",
            "Sous réserve de"
        ]
    },
    'conclusion': {
        'plainte': [
            "C\'est dans ces conditions que je sollicite l\'ouverture d\'une enquête",
            "Au vu de ces éléments, je demande que des poursuites soient engagées",
            "Je me constitue partie civile et demande réparation de mon préjudice",
            "En conséquence, je vous prie de bien vouloir donner suite à ma plainte",
            "Je sollicite que toutes suites utiles soient données à la présente"
        ],
        'conclusions': [
            "PAR CES MOTIFS, plaise au Tribunal de :",
            "C\'est pourquoi il est demandé au Tribunal de :",
            "En conséquence de tout ce qui précède, le Tribunal est prié de :",
            "Au vu de l\'ensemble de ces éléments, il y a lieu de :",
            "C\'est dans ces conditions qu\'il est demandé au Tribunal de :"
        ],
        'courrier': [
            "Je vous prie d\'agréer, {destinataire}, l\'expression de mes salutations distinguées",
            "Veuillez croire, {destinataire}, en l\'assurance de ma considération distinguée",
            "Je vous prie de recevoir, {destinataire}, mes salutations respectueuses",
            "Restant à votre disposition pour tout complément d\'information",
            "Dans l\'attente de votre retour, je vous prie d\'agréer"
        ]
    },
    'formules_types': {
        'demande_communication': [
            "Je vous serais reconnaissant de bien vouloir me communiquer",
            "Je vous prie de bien vouloir me transmettre",
            "Je sollicite la communication de",
            "Il vous est demandé de produire",
            "Vous êtes prié de communiquer"
        ],
        'demande_delai': [
            "Je sollicite un délai supplémentaire pour",
            "Je vous prie de bien vouloir m\'accorder un délai",
            "Un délai supplémentaire est nécessaire pour",
            "Je demande la prorogation du délai pour",
            "Il est sollicité un report de délai"
        ],
        'contestation': [
            "Je conteste formellement",
            "Je m\'inscris en faux contre",
            "Je m\'oppose à",
            "Je forme opposition à",
            "J\'entends contester"
        ],
        'reservation': [
            "Sous toutes réserves",
            "Toutes mes réserves étant expressément maintenues",
            "Sans reconnaissance préjudiciable",
            "Sans que cela puisse me porter préjudice",
            "Sous réserve de tous mes droits"
        ]
    },
    'civilites': {
        'magistrat': {
            'debut': [
                "Monsieur le Président,",
                "Madame la Présidente,",
                "Monsieur le Juge,",
                "Madame la Juge,",
                "Monsieur le Procureur de la République,",
                "Madame la Procureure de la République,"
            ],
            'fin': [
                "Je vous prie d\'agréer, Monsieur le Président, l\'expression de ma haute considération",
                "Veuillez agréer, Madame la Présidente, l\'expression de mes sentiments respectueux",
                "Je vous prie de croire, Monsieur le Procureur, en l\'assurance de ma haute considération"
            ]
        },
        'confrere': {
            'debut': [
                "Cher Confrère,",
                "Chère Consœur,",
                "Maître,",
                "Mon cher Confrère,",
                "Ma chère Consœur,"
            ],
            'fin': [
                "Je vous prie de croire, Cher Confrère, en l\'assurance de mes sentiments confraternels dévoués",
                "Bien confraternellement",
                "Avec mes sentiments confraternels les meilleurs",
                "Veuillez agréer, Chère Consœur, mes salutations confraternelles"
            ]
        },
        'client': {
            'debut': [
                "Madame,",
                "Monsieur,",
                "Madame, Monsieur,",
                "Cher Client,",
                "Chère Cliente,"
            ],
            'fin': [
                "Je reste à votre entière disposition pour tout complément d\'information",
                "N\'hésitez pas à me contacter pour toute question",
                "Je vous prie d\'agréer, Madame, l\'expression de mes salutations distinguées",
                "Cordialement"
            ]
        }
    }
}

# ========== PATTERNS D'ARGUMENTATION ==========

ARGUMENTATION_PATTERNS = {
    'structure_argument': {
        'syllogisme': {
            'pattern': [
                "Majeure : {principe_general}",
                "Mineure : {application_cas}",
                "Conclusion : {resultat}"
            ],
            'exemple': [
                "Majeure : Tout contrat légalement formé tient lieu de loi à ceux qui l\'ont fait",
                "Mineure : En l\'espèce, un contrat a été valablement conclu entre les parties",
                "Conclusion : Ce contrat doit donc être exécuté selon ses termes"
            ]
        },
        'demonstration': {
            'pattern': [
                "Il sera démontré que {these}",
                "En effet, {argument_1}",
                "De plus, {argument_2}",
                "Par ailleurs, {argument_3}",
                "Il en résulte que {conclusion}"
            ]
        },
        'refutation': {
            'pattern': [
                "La partie adverse soutient que {these_adverse}",
                "Cependant, cette argumentation ne résiste pas à l\'analyse",
                "En effet, {contre_argument_1}",
                "De surcroît, {contre_argument_2}",
                "Par conséquent, {conclusion_refutation}"
            ]
        }
    },
    
    'techniques_persuasion': {
        'argument_autorite': [
            "Selon la jurisprudence constante de {juridiction}",
            "Comme l\'a rappelé {autorite} dans {reference}",
            "La doctrine unanime considère que",
            "Il est de jurisprudence constante que"
        ],
        'argument_analogie': [
            "Par analogie avec {situation_similaire}",
            "À l\'instar de {precedent}",
            "Comme dans l\'affaire {reference}",
            "De la même manière que"
        ],
        'argument_a_fortiori': [
            "A fortiori",
            "À plus forte raison",
            "D\'autant plus que",
            "Cela est d\'autant plus vrai que"
        ],
        'argument_a_contrario': [
            "A contrario",
            "En sens inverse",
            "Par opposition",
            "À l\'inverse"
        ]
    },
    
    'enchainements_logiques': {
        'causalite': [
            "dès lors que",
            "dans la mesure où",
            "attendu que",
            "considérant que",
            "puisque",
            "car",
            "en raison de"
        ],
        'consequence': [
            "par conséquent",
            "en conséquence",
            "il s\'ensuit que",
            "partant",
            "de sorte que",
            "si bien que",
            "avec pour effet que"
        ],
        'condition': [
            "à condition que",
            "sous réserve que",
            "pour autant que",
            "dans l\'hypothèse où",
            "au cas où",
            "si et seulement si"
        ],
        'concession': [
            "bien que",
            "quoique",
            "même si",
            "en dépit de",
            "malgré",
            "nonobstant"
        ]
    },
    
    'formules_argumentatives': {
        'introduction_argument': [
            "Il convient d\'examiner",
            "Il y a lieu de relever",
            "Il importe de souligner",
            "Il est nécessaire de rappeler",
            "Force est de constater"
        ],
        'renforcement': [
            "Il est manifeste que",
            "Il ne fait aucun doute que",
            "Il est incontestable que",
            "Il apparaît clairement que",
            "Il est évident que"
        ],
        'nuance': [
            "Il semble que",
            "Il apparaît que",
            "Il est permis de penser que",
            "On peut considérer que",
            "Il n\'est pas exclu que"
        ],
        'opposition': [
            "Il ne saurait être soutenu que",
            "C\'est à tort que",
            "Contrairement à ce qui est prétendu",
            "Il est erroné d\'affirmer que",
            "Cette thèse ne peut prospérer"
        ]
    },
    
    'structures_complexes': {
        'plan_deux_parties': {
            'structure': [
                "I. {titre_partie_1}",
                "A. {sous_partie_1a}",
                "B. {sous_partie_1b}",
                "II. {titre_partie_2}",
                "A. {sous_partie_2a}",
                "B. {sous_partie_2b}"
            ],
            'exemples': [
                {
                    'titre': "Sur la responsabilité contractuelle",
                    'partie_1': "L\'existence d\'un manquement contractuel",
                    'partie_2': "Le préjudice résultant du manquement"
                },
                {
                    'titre': "Sur la recevabilité et le fond",
                    'partie_1': "Sur la recevabilité de la demande",
                    'partie_2': "Sur le bien-fondé de la demande"
                }
            ]
        },
        'cascade_argumentative': {
            'pattern': [
                "Premièrement, {argument_principal}",
                "Deuxièmement, et subsidiairement, {argument_subsidiaire_1}",
                "Troisièmement, et plus subsidiairement encore, {argument_subsidiaire_2}",
                "En tout état de cause, {argument_final}"
            ]
        }
    },
    
    'liaisons_juridiques': {
        'articulation_moyens': [
            "S\'agissant du premier moyen",
            "Concernant le second moyen",
            "Quant au moyen tiré de",
            "Sur le moyen unique",
            "Au titre du moyen principal"
        ],
        'articulation_demandes': [
            "À titre principal",
            "À titre subsidiaire",
            "À titre infiniment subsidiaire",
            "En tout état de cause",
            "Subsidiairement"
        ],
        'references_pieces': [
            "Comme en atteste la pièce n°{numero}",
            "Il ressort de la pièce n°{numero} que",
            "La pièce n°{numero} démontre que",
            "Ainsi qu\'il résulte de la pièce n°{numero}",
            "Voir en ce sens pièce n°{numero}"
        ]
    },
    
    'modeles_demonstration': {
        'preuve_negative': {
            'pattern': [
                "Il n\'est rapporté aucune preuve de {element}",
                "Aucun élément ne permet d\'établir {fait}",
                "La partie adverse ne démontre pas {allegation}",
                "Il n\'est justifié d\'aucun {element_requis}"
            ]
        },
        'preuve_positive': {
            'pattern': [
                "Il est établi que {fait}",
                "Les pièces versées démontrent {element}",
                "Il résulte des éléments du dossier que {conclusion}",
                "La preuve est rapportée de {fait_prouve}"
            ]
        },
        'charge_preuve': {
            'pattern': [
                "Il appartient à {partie} de démontrer {element}",
                "La charge de la preuve incombe à {partie}",
                "{partie} doit rapporter la preuve de {allegation}",
                "C\'est à {partie} qu\'il revient d\'établir {fait}"
            ]
        }
    },
    
    'rhetorique_juridique': {
        'questions_rhetoriques': [
            "Comment soutenir que {these} alors que {fait_contraire} ?",
            "Peut-on sérieusement prétendre que {allegation} ?",
            "N\'est-il pas évident que {evidence} ?",
            "Quelle crédibilité accorder à {argument} ?"
        ],
        'mise_en_perspective': [
            "Il convient de replacer {element} dans son contexte",
            "Cette situation doit être appréciée au regard de {critere}",
            "Il faut considérer {fait} à la lumière de {principe}",
            "Cela s\'inscrit dans le cadre de {contexte_general}"
        ],
        'formules_conclusives': [
            "Il résulte de tout ce qui précède que",
            "Au vu de l\'ensemble de ces éléments",
            "En définitive",
            "Pour toutes ces raisons",
            "C\'est dans ces conditions que"
        ]
    }
}

# ========== CONFIGURATIONS D'ANALYSE ==========

ANALYSIS_CONFIGS = {
    'types_analyse': {
        'general': {
            'nom': "Analyse générale",
            'description': "Analyse complète d\'un document ou d\'une situation juridique",
            'sections': [
                'contexte',
                'qualification_juridique',
                'points_cles',
                'risques',
                'recommandations'
            ],
            'prompt_template': "Analyser de manière approfondie {document} en identifiant les enjeux juridiques principaux"
        },
        'risques': {
            'nom': "Analyse des risques",
            'description': "Identification et évaluation des risques juridiques",
            'sections': [
                'risques_identifies',
                'probabilite_realisation',
                'impact_potentiel',
                'mesures_preventives',
                'plan_action'
            ],
            'niveaux_risque': ['faible', 'moyen', 'élevé', 'critique'],
            'matrice_evaluation': {
                'probabilite': ['rare', 'possible', 'probable', 'certain'],
                'impact': ['négligeable', 'modéré', 'important', 'catastrophique']
            }
        },
        'conformite': {
            'nom': "Analyse de conformité",
            'description': "Vérification de la conformité aux obligations légales",
            'sections': [
                'obligations_identifiees',
                'niveau_conformite',
                'ecarts_constates',
                'actions_correctives',
                'calendrier_mise_conformite'
            ],
            'criteres_evaluation': [
                'respect_delais',
                'formalites_accomplies',
                'documents_requis',
                'autorisations_obtenues'
            ]
        },
        'strategie': {
            'nom': "Analyse stratégique",
            'description': "Élaboration de stratégies juridiques",
            'sections': [
                'objectifs',
                'options_disponibles',
                'avantages_inconvenients',
                'recommandation_strategique',
                'plan_execution'
            ],
            'facteurs_decision': [
                'probabilite_succes',
                'cout_financier',
                'duree_procedure',
                'impact_reputation',
                'complexite_execution'
            ]
        },
        'infractions': {
            'nom': "Analyse des infractions",
            'description': "Identification et qualification des infractions pénales",
            'sections': [
                'faits_analyses',
                'qualifications_possibles',
                'elements_constitutifs',
                'preuves_disponibles',
                'sanctions_encourues'
            ],
            'elements_analyser': [
                'element_legal',
                'element_materiel',
                'element_moral',
                'circonstances_aggravantes',
                'causes_exoneration'
            ]
        },
        'jurisprudence': {
            'nom': "Analyse jurisprudentielle",
            'description': "Analyse de l\'état de la jurisprudence sur une question",
            'sections': [
                'question_posee',
                'jurisprudence_constante',
                'evolutions_recentes',
                'divergences_jurisprudentielles',
                'tendances_futures'
            ],
            'sources_analyser': [
                'cour_cassation',
                'conseil_etat',
                'cours_appel',
                'doctrine',
                'droit_compare'
            ]
        }
    },
    
    'criteres_analyse': {
        'juridique': {
            'pertinence_juridique': {
                'description': "Pertinence des arguments juridiques",
                'indicateurs': [
                    'fondement_textuel',
                    'coherence_jurisprudence',
                    'logique_argumentation'
                ],
                'echelle': [1, 10]
            },
            'solidite_fondements': {
                'description': "Solidité des fondements juridiques",
                'indicateurs': [
                    'textes_applicables',
                    'jurisprudence_etablie',
                    'doctrine_majoritaire'
                ],
                'echelle': [1, 10]
            },
            'exhaustivite': {
                'description': "Exhaustivité de l\'analyse",
                'indicateurs': [
                    'tous_aspects_couverts',
                    'exceptions_identifiees',
                    'cas_particuliers_traites'
                ],
                'echelle': [1, 10]
            }
        },
        'strategique': {
            'rapport_cout_benefice': {
                'description': "Rapport coût/bénéfice de la stratégie",
                'facteurs': [
                    'cout_procedure',
                    'duree_estimee',
                    'gains_potentiels',
                    'risques_associes'
                ]
            },
            'faisabilite': {
                'description': "Faisabilité de la mise en œuvre",
                'facteurs': [
                    'ressources_necessaires',
                    'competences_requises',
                    'delais_respecter',
                    'contraintes_pratiques'
                ]
            },
            'impact': {
                'description': "Impact potentiel",
                'dimensions': [
                    'impact_juridique',
                    'impact_financier',
                    'impact_reputationnel',
                    'impact_operationnel'
                ]
            }
        }
    },
    
    'methodes_analyse': {
        'swot_juridique': {
            'nom': "Analyse SWOT juridique",
            'composantes': {
                'forces': "Points forts de la position juridique",
                'faiblesses': "Points faibles et vulnérabilités",
                'opportunites': "Opportunités juridiques à exploiter",
                'menaces': "Risques et menaces juridiques"
            },
            'application': [
                'contentieux',
                'negociation',
                'structuration',
                'compliance'
            ]
        },
        'arbre_decision': {
            'nom': "Arbre de décision juridique",
            'elements': [
                'decision_initiale',
                'options_disponibles',
                'consequences_chaque_option',
                'probabilites_succes',
                'recommandation_finale'
            ]
        },
        'matrice_risques': {
            'nom': "Matrice des risques juridiques",
            'axes': {
                'probabilite': ['très faible', 'faible', 'moyenne', 'élevée', 'très élevée'],
                'impact': ['négligeable', 'mineur', 'modéré', 'majeur', 'catastrophique']
            },
            'zones': {
                'acceptable': "Risque acceptable - surveillance simple",
                'attention': "Risque sous surveillance - mesures préventives",
                'critique': "Risque critique - action immédiate requise"
            }
        }
    },
    
    'templates_analyse': {
        'note_synthese': {
            'structure': [
                "## Objet de l\'analyse",
                "## Résumé exécutif",
                "## Contexte factuel",
                "## Analyse juridique",
                "### Points de droit",
                "### Application aux faits",
                "## Risques identifiés",
                "## Recommandations",
                "## Conclusion"
            ],
            'longueur_cible': 1500
        },
        'memorandum': {
            'structure': [
                "# MÉMORANDUM",
                "**À :** {destinataire}",
                "**De :** {auteur}",
                "**Date :** {date}",
                "**Objet :** {objet}",
                "",
                "## Question posée",
                "## Réponse synthétique",
                "## Analyse détaillée",
                "## Précédents pertinents",
                "## Recommandations pratiques"
            ],
            'style': 'concis et direct'
        },
        'rapport_diligence': {
            'structure': [
                "# RAPPORT DE DUE DILIGENCE",
                "## 1. Synthèse",
                "## 2. Méthodologie",
                "## 3. Documents analysés",
                "## 4. Constats",
                "### 4.1 Points positifs",
                "### 4.2 Points d\'attention",
                "### 4.3 Risques majeurs",
                "## 5. Recommandations",
                "## 6. Réserves",
                "## Annexes"
            ],
            'elements_verifier': [
                'structure_juridique',
                'contrats_majeurs',
                'litiges_en_cours',
                'conformite_reglementaire',
                'propriete_intellectuelle',
                'aspects_sociaux'
            ]
        }
    },
    
    'indicateurs_qualite': {
        'completude': {
            'description': "Analyse complète de tous les aspects",
            'criteres': [
                'tous_points_traites',
                'sources_citees',
                'exceptions_mentionnees',
                'alternatives_explorees'
            ]
        },
        'clarte': {
            'description': "Clarté et lisibilité de l\'analyse",
            'criteres': [
                'structure_logique',
                'langage_accessible',
                'synthese_presente',
                'conclusions_claires'
            ]
        },
        'pertinence': {
            'description': "Pertinence pratique de l\'analyse",
            'criteres': [
                'reponse_question_posee',
                'recommandations_actionnables',
                'prise_compte_contexte',
                'utilite_operationnelle'
            ]
        },
        'fiabilite': {
            'description': "Fiabilité juridique de l\'analyse",
            'criteres': [
                'sources_a_jour',
                'jurisprudence_recente',
                'interpretations_consensuelles',
                'reserves_appropriees'
            ]
        }
    },
    
    'formats_sortie': {
        'executive_summary': {
            'longueur_max': 500,
            'sections': ['enjeu', 'analyse', 'risques', 'recommandation'],
            'style': 'bullet_points'
        },
        'analyse_detaillee': {
            'longueur_min': 2000,
            'sections': 'completes',
            'style': 'paragraphes_structures',
            'citations': 'obligatoires'
        },
        'tableau_synthese': {
            'format': 'tableau',
            'colonnes': ['aspect', 'analyse', 'risque', 'action'],
            'tri': 'par_priorite'
        },
        'presentation': {
            'format': 'slides',
            'nombre_slides': '10-15',
            'contenu': ['titre', 'synthese', 'details', 'conclusion'],
            'visuels': 'graphiques_recommandes'
        }
    }
}

# ========== CLASSE DE CONFIGURATION PRINCIPALE ==========

class DocumentConfigurations:
    """Gestionnaire des configurations de templates"""
    
    # Configuration pour les plaintes
    PLAINTE_CONFIG = {
        'sections': [
            {
                'id': 'en_tete',
                'title': 'En-tête',
                'required': True,
                'fields': [
                    {'name': 'tribunal', 'type': 'text', 'label': 'Tribunal compétent'},
                    {'name': 'date', 'type': 'date', 'label': 'Date'},
                    {'name': 'reference', 'type': 'text', 'label': 'Référence'}
                ]
            },
            {
                'id': 'parties',
                'title': 'Identification des parties',
                'required': True,
                'fields': [
                    {'name': 'plaignant', 'type': 'party', 'label': 'Plaignant'},
                    {'name': 'mis_en_cause', 'type': 'party', 'label': 'Mis en cause'}
                ]
            },
            {
                'id': 'faits',
                'title': 'Exposé des faits',
                'required': True,
                'content_type': 'narrative',
                'min_length': 500
            },
            {
                'id': 'infractions',
                'title': 'Qualification juridique',
                'required': True,
                'fields': [
                    {'name': 'infractions', 'type': 'multi_select', 'label': 'Infractions'}
                ]
            },
            {
                'id': 'prejudice',
                'title': 'Préjudice subi',
                'required': True,
                'fields': [
                    {'name': 'montant', 'type': 'currency', 'label': 'Montant du préjudice'},
                    {'name': 'description', 'type': 'textarea', 'label': 'Description'}
                ]
            },
            {
                'id': 'demandes',
                'title': 'Demandes',
                'required': True,
                'content_type': 'list'
            }
        ],
        'style': {
            'format': 'formal',
            'tone': 'juridique',
            'references': 'codes_penaux'
        }
    }
    
    # Configuration pour les conclusions
    CONCLUSIONS_CONFIG = {
        'sections': [
            {
                'id': 'rappel_procedure',
                'title': 'Rappel de la procédure',
                'required': True,
                'auto_generate': True
            },
            {
                'id': 'faits_procedure',
                'title': 'Faits et procédure',
                'required': True,
                'subsections': [
                    'chronologie',
                    'actes_procedure',
                    'incidents'
                ]
            },
            {
                'id': 'discussion',
                'title': 'Discussion',
                'required': True,
                'subsections': [
                    'moyens_fond',
                    'moyens_forme',
                    'reponse_adverse'
                ]
            },
            {
                'id': 'dispositif',
                'title': 'Dispositif',
                'required': True,
                'format': 'numbered_list'
            }
        ],
        'numbering': {
            'style': 'decimal',
            'levels': 3,
            'format': '1. / 1.1. / 1.1.1.'
        }
    }
    
    # Configuration pour les courriers
    COURRIER_CONFIG = {
        'types': {
            'mise_en_demeure': {
                'tone': 'ferme',
                'structure': [
                    'objet',
                    'rappel_faits',
                    'obligations',
                    'delai',
                    'consequences'
                ]
            },
            'reponse_contradictoire': {
                'tone': 'courtois',
                'structure': [
                    'accusé_reception',
                    'analyse_demandes',
                    'position_client',
                    'propositions'
                ]
            },
            'notification': {
                'tone': 'neutre',
                'structure': [
                    'objet',
                    'information',
                    'modalites',
                    'contact'
                ]
            }
        }
    }
    
    # Configuration pour l'analyse
    ANALYSE_CONFIG = {
        'criteres': [
            {
                'id': 'forces',
                'title': 'Points forts',
                'icon': '✅',
                'weight': 1.0
            },
            {
                'id': 'faiblesses',
                'title': 'Points faibles',
                'icon': '⚠️',
                'weight': 1.0
            },
            {
                'id': 'opportunites',
                'title': 'Opportunités',
                'icon': '💡',
                'weight': 0.8
            },
            {
                'id': 'risques',
                'title': 'Risques',
                'icon': '🚨',
                'weight': 1.2
            }
        ],
        'scoring': {
            'methode': 'pondérée',
            'echelle': [1, 10],
            'seuils': {
                'favorable': 7,
                'neutre': 5,
                'defavorable': 3
            }
        }
    }
    
    # Templates de phrases juridiques
    PHRASES_JURIDIQUES = {
        'introduction': {
            'plainte': [
                "J'ai l'honneur de porter plainte contre {partie} pour les faits suivants :",
                "Par la présente, je souhaite porter à votre connaissance les agissements délictueux de {partie}",
                "Je soussigné(e), {plaignant}, porte plainte pour les faits ci-après exposés"
            ],
            'conclusions': [
                "Pour les motifs ci-après développés, le {demandeur} a l'honneur d'exposer ce qui suit :",
                "Il sera démontré dans les présentes conclusions que {these_principale}",
                "Les développements qui suivent établiront que {objectif}"
            ],
            'assignation': [
                "L'an {annee} et le {date}, à la requête de {demandeur}",
                "Nous, {huissier}, huissier de justice, avons donné assignation à {defendeur}",
                "Par exploit de notre ministère, assignation est donnée à {partie}"
            ]
        },
        'transition': {
            'moreover': [
                "En outre,",
                "Par ailleurs,",
                "De surcroît,",
                "Qui plus est,"
            ],
            'consequence': [
                "En conséquence,",
                "Par conséquent,",
                "Il s'ensuit que",
                "Partant,"
            ],
            'opposition': [
                "Cependant,",
                "Néanmoins,",
                "Pour autant,",
                "Toutefois,"
            ]
        },
        'conclusion': {
            'plainte': [
                "C'est dans ces conditions que je sollicite l'ouverture d'une enquête",
                "Au vu de ces éléments, je demande que des poursuites soient engagées",
                "Je me constitue partie civile et demande réparation de mon préjudice"
            ],
            'conclusions': [
                "PAR CES MOTIFS, plaise au Tribunal de :",
                "C'est pourquoi il est demandé au Tribunal de :",
                "En conséquence de tout ce qui précède, le Tribunal est prié de :"
            ]
        }
    }
    
    # Formules de politesse
    FORMULES_POLITESSE = {
        'courrier': {
            'debut': {
                'formel': [
                    "Monsieur le Président,",
                    "Madame, Monsieur,",
                    "Maître,"
                ],
                'neutre': [
                    "Madame, Monsieur,",
                    "Cher Confrère,",
                    "Chère Consœur,"
                ]
            },
            'fin': {
                'formel': [
                    "Je vous prie d'agréer, Monsieur le Président, l'expression de ma haute considération.",
                    "Veuillez agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
                    "Je vous prie de croire, Maître, en l'assurance de mes sentiments respectueux."
                ],
                'neutre': [
                    "Cordialement,",
                    "Bien à vous,",
                    "Sincères salutations,"
                ]
            }
        }
    }
    
    # Configuration des pièces
    PIECES_CONFIG = {
        'categories': [
            {
                'id': 'contrats',
                'title': 'Contrats et conventions',
                'types': ['contrat', 'avenant', 'convention', 'protocole']
            },
            {
                'id': 'correspondances',
                'title': 'Correspondances',
                'types': ['courrier', 'email', 'mise_en_demeure', 'notification']
            },
            {
                'id': 'expertises',
                'title': 'Expertises et rapports',
                'types': ['expertise', 'rapport', 'constat', 'audit']
            },
            {
                'id': 'comptables',
                'title': 'Documents comptables',
                'types': ['facture', 'devis', 'bon_commande', 'releve']
            },
            {
                'id': 'judiciaires',
                'title': 'Actes judiciaires',
                'types': ['assignation', 'conclusions', 'jugement', 'ordonnance']
            }
        ],
        'numerotation': {
            'format': 'Pièce n°{numero}',
            'groupement': 'par_categorie',
            'tri': 'chronologique'
        }
    }
    
    # Styles de rédaction
    STYLES_REDACTION = {
        'formel': {
            'vocabulaire': 'soutenu',
            'phrases': 'complexes',
            'ton': 'distant',
            'connecteurs': ['nonobstant', 'attendu que', 'considérant']
        },
        'synthetique': {
            'vocabulaire': 'accessible',
            'phrases': 'courtes',
            'ton': 'direct',
            'connecteurs': ['en effet', 'par ailleurs', 'donc']
        },
        'persuasif': {
            'vocabulaire': 'imagé',
            'phrases': 'rythmées',
            'ton': 'convaincant',
            'connecteurs': ['manifestement', 'indubitablement', 'à l\'évidence']
        },
        'technique': {
            'vocabulaire': 'précis',
            'phrases': 'structurées',
            'ton': 'neutre',
            'connecteurs': ['conformément à', 'en application de', 'aux termes de']
        },
        'pedagogique': {
            'vocabulaire': 'clair',
            'phrases': 'simples',
            'ton': 'explicatif',
            'connecteurs': ['ainsi', 'c\'est-à-dire', 'en d\'autres termes']
        }
    }
    
    # Configuration des timelines
    TIMELINE_CONFIG = {
        'elements': [
            {
                'type': 'evenement',
                'icon': '📅',
                'couleur': '#3498db'
            },
            {
                'type': 'document',
                'icon': '📄',
                'couleur': '#2ecc71'
            },
            {
                'type': 'procedure',
                'icon': '⚖️',
                'couleur': '#e74c3c'
            },
            {
                'type': 'expertise',
                'icon': '🔍',
                'couleur': '#f39c12'
            }
        ],
        'affichage': {
            'orientation': 'verticale',
            'groupement': 'par_mois',
            'details': 'au_survol'
        }
    }
    
    # Mapping des infractions
    INFRACTIONS_MAPPING = {
        'escroquerie': {
            'article': '313-1',
            'code': 'pénal',
            'peine_max': '5 ans et 375 000 €',
            'elements': ['manœuvres frauduleuses', 'tromperie', 'remise de biens']
        },
        'abus_de_confiance': {
            'article': '314-1',
            'code': 'pénal',
            'peine_max': '3 ans et 375 000 €',
            'elements': ['détournement', 'préjudice', 'remise volontaire']
        },
        'abus_de_biens_sociaux': {
            'article': 'L241-3',
            'code': 'commerce',
            'peine_max': '5 ans et 375 000 €',
            'elements': ['usage contraire', 'intérêt personnel', 'mauvaise foi']
        },
        'faux': {
            'article': '441-1',
            'code': 'pénal',
            'peine_max': '3 ans et 45 000 €',
            'elements': ['altération', 'vérité', 'préjudice']
        }
    }
    
    # Configuration des validations
    VALIDATION_RULES = {
        'plainte': {
            'min_sections': 4,
            'required_fields': ['plaignant', 'mis_en_cause', 'faits', 'infractions'],
            'min_words': 500
        },
        'conclusions': {
            'min_sections': 3,
            'required_fields': ['parties', 'faits', 'dispositif'],
            'min_words': 1000
        },
        'assignation': {
            'min_sections': 5,
            'required_fields': ['demandeur', 'defendeur', 'tribunal', 'date_audience'],
            'min_words': 800
        }
    }
    
    # Templates d'emails
    EMAIL_TEMPLATES = {
        "envoi_pieces": {
            "objet": "Transmission de pièces - Dossier {reference}",
            "corps": "Maître,\n\nSuite à notre entretien de ce jour, je vous prie de bien vouloir trouver ci-joint les pièces suivantes :\n{liste_pieces}\n\nCes documents viennent compléter le dossier référencé {reference}.\n\nJe reste à votre disposition pour tout complément concernant ce dossier.\n\nBien cordialement,\n{expediteur}"
        },
        "demande_informations": {
            "objet": "Demande de renseignements complémentaires - {dossier}",
            "corps": "Cher Confrère,\n\nDans le cadre du dossier {dossier}, il me faudrait les informations suivantes :\n{liste_questions}\n\nJe vous serais reconnaissant de bien vouloir me faire parvenir ces éléments dans les meilleurs délais.\n\nBien confraternellement,\n{expediteur}"
        }
    }
    
    # Configuration des exports
    EXPORT_CONFIG = {
        'formats': {
            'word': {
                'extension': '.docx',
                'template': 'cabinet_template.docx',
                'styles': True
            },
            'pdf': {
                'extension': '.pdf',
                'compression': True,
                'protection': False
            },
            'bundle': {
                'extension': '.zip',
                'inclure_pieces': True,
                'structure': 'hierarchique'
            }
        },
        'naming': {
            'pattern': '{date}_{type}_{reference}_{version}',
            'date_format': 'YYYYMMDD',
            'version_format': 'v{numero}'
        }
    }
    
    # Actions rapides
    QUICK_ACTIONS = {
        'redaction': [
            {'id': 'plainte', 'label': 'Nouvelle plainte', 'icon': '📝'},
            {'id': 'conclusions', 'label': 'Conclusions', 'icon': '📋'},
            {'id': 'assignation', 'label': 'Assignation', 'icon': '📨'},
            {'id': 'courrier', 'label': 'Courrier', 'icon': '✉️'}
        ],
        'analyse': [
            {'id': 'forces_faiblesses', 'label': 'Analyse SWOT', 'icon': '📊'},
            {'id': 'chronologie', 'label': 'Timeline', 'icon': '📅'},
            {'id': 'pieces', 'label': 'Inventaire pièces', 'icon': '📁'},
            {'id': 'synthese', 'label': 'Synthèse', 'icon': '📝'}
        ],
        'gestion': [
            {'id': 'import', 'label': 'Importer', 'icon': '📥'},
            {'id': 'export', 'label': 'Exporter', 'icon': '📤'},
            {'id': 'email', 'label': 'Envoyer', 'icon': '📧'},
            {'id': 'planning', 'label': "Plan d'action", 'icon': '🎯'}
        ]
    }
    
    # Méthodes de classe
    @classmethod
    def get_template_config(cls, template_type: str) -> Dict[str, Any]:
        """Récupère la configuration d'un template"""
        configs = {
            'plainte': cls.PLAINTE_CONFIG,
            'conclusions': cls.CONCLUSIONS_CONFIG,
            'courrier': cls.COURRIER_CONFIG,
            'analyse': cls.ANALYSE_CONFIG
        }
        return configs.get(template_type, {})
    
    @classmethod
    def get_phrases(cls, category: str, subcategory: str = None) -> List[str]:
        """Récupère des phrases types"""
        if subcategory:
            return cls.PHRASES_JURIDIQUES.get(category, {}).get(subcategory, [])
        return cls.PHRASES_JURIDIQUES.get(category, {})
    
    @classmethod
    def get_validation_rules(cls, doc_type: str) -> Dict[str, Any]:
        """Récupère les règles de validation"""
        return cls.VALIDATION_RULES.get(doc_type, {})
    
    @classmethod
    def get_infraction_details(cls, infraction: str) -> Dict[str, Any]:
        """Récupère les détails d'une infraction"""
        # Normaliser la clé
        key = infraction.lower().replace(' ', '_').replace("'", "")
        return cls.INFRACTIONS_MAPPING.get(key, {})
    
    @classmethod
    def get_export_format(cls, format_name: str) -> Dict[str, Any]:
        """Récupère la configuration d'export"""
        return cls.EXPORT_CONFIG['formats'].get(format_name, {})
    
    @classmethod
    def get_quick_actions(cls, category: str = None) -> List[Dict[str, str]]:
        """Récupère les actions rapides"""
        if category:
            return cls.QUICK_ACTIONS.get(category, [])
        
        # Retourner toutes les actions
        all_actions = []
        for actions in cls.QUICK_ACTIONS.values():
            all_actions.extend(actions)
        return all_actions
    
    @classmethod
    def validate_document(cls, doc_type: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Valide un document selon les règles"""
        rules = cls.get_validation_rules(doc_type)
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Vérifier les champs requis
        for field in rules.get('required_fields', []):
            if field not in document or not document[field]:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Champ requis manquant : {field}")
        
        # Vérifier le nombre de mots
        content = document.get('content', '')
        word_count = len(content.split())
        min_words = rules.get('min_words', 0)
        
        if word_count < min_words:
            validation_result['warnings'].append(
                f"Document trop court : {word_count} mots (minimum recommandé : {min_words})"
            )
        
        return validation_result
    
    @classmethod
    def format_piece_number(cls, numero: int, categorie: str = None) -> str:
        """Formate un numéro de pièce"""
        pattern = cls.PIECES_CONFIG['numerotation']['format']
        return pattern.format(numero=numero)
    
    @classmethod
    def get_style_config(cls, style_name: str) -> Dict[str, Any]:
        """Récupère la configuration d'un style"""
        return cls.STYLES_REDACTION.get(style_name, cls.STYLES_REDACTION['synthetique'])

# ========== EXPORTS ==========

__all__ = [
    'DEFAULT_LETTERHEADS',
    'BUILTIN_DOCUMENT_TEMPLATES',
    'DEFAULT_STYLE_CONFIGS',
    'FORMULES_JURIDIQUES',
    'ARGUMENTATION_PATTERNS',
    'ANALYSIS_CONFIGS',
    'DocumentConfigurations'
]