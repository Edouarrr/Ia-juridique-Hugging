from typing import Dict, List, Any
import json
from modules.dataclasses import StyleConfig, DocumentTemplate, TypeDocument, StyleRedaction, LetterheadTemplate
from datetime import datetime

# ========== PAPIERS EN-TÊTE PAR DÉFAUT ==========

DEFAULT_LETTERHEADS = [
    LetterheadTemplate(
        name="Cabinet classique",
        header_content="""CABINET D'AVOCATS
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
[ADRESSE LIGNE 1] • [ADRESSE LIGNE 2]
T. [TÉLÉPHONE] • F. [FAX] • [EMAIL] • [SITE WEB]""",
        footer_content="""[NOM CABINET] • Société d'avocats • Barreau de [VILLE]
SIRET : [SIRET] • TVA Intracommunautaire : [TVA]""",
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
        footer_content="""[ADRESSE] • [CODE POSTAL] [VILLE]
Barreau de [VILLE] • Toque [NUMÉRO]""",
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
        header_content="""ÉTUDE D'AVOCATS
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
Société d'exercice libéral par actions simplifiée d'avocats
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
        footer_content="""Palais de Justice de [VILLE] • Case [NUMÉRO]
SELARL au capital de [CAPITAL] € • RCS [VILLE] [RCS] • TVA : [TVA]""",
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
SCP D'AVOCATS • PALAIS DE JUSTICE, CASE# models/configurations.py
"""Configurations pour les templates de génération de documents"""

from typing import Dict, List, Any
import json
from modules.dataclasses import StyleConfig, DocumentTemplate, TypeDocument, StyleRedaction

# ========== TEMPLATES DE DOCUMENTS INTÉGRÉS ==========

BUILTIN_DOCUMENT_TEMPLATES = [
    DocumentTemplate(
        id="plainte_simple",
        name="Plainte simple",
        type=TypeDocument.PLAINTE,
        structure=[
            "Monsieur le Procureur de la République,",
            "",
            "J'ai l'honneur de porter plainte contre [MIS EN CAUSE] pour les faits suivants :",
            "",
            "## EXPOSÉ DES FAITS",
            "[Description détaillée des faits]",
            "",
            "## PRÉJUDICE SUBI",
            "[Description du préjudice]",
            "",
            "## DEMANDES",
            "En conséquence, je sollicite :",
            "- L'ouverture d'une enquête",
            "- [Autres demandes]",
            "",
            "Je me tiens à votre disposition pour tout complément d'information.",
            "",
            "Je vous prie d'agréer, Monsieur le Procureur de la République, l'expression de ma haute considération.",
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
        type=TypeDocument.PLAINTE_CPC,
        structure=[
            "Monsieur le Doyen des Juges d'Instruction,",
            "",
            "J'ai l'honneur de déposer entre vos mains une plainte avec constitution de partie civile contre :",
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
            "- Ordonner l'ouverture d'une information judiciaire",
            "- [Autres demandes]",
            "",
            "Sous toutes réserves",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.FORMEL,
        category="Pénal",
        description="Modèle de plainte avec constitution de partie civile pour saisir le juge d'instruction"
    ),
    
    DocumentTemplate(
        id="conclusions_demandeur",
        name="Conclusions pour demandeur",
        type=TypeDocument.CONCLUSIONS,
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
            "[Application aux faits de l'espèce]",
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
        type=TypeDocument.ASSIGNATION,
        structure=[
            "L'AN [ANNÉE] ET LE [DATE]",
            "",
            "À LA REQUÊTE DE :",
            "[IDENTIFICATION COMPLÈTE DU DEMANDEUR]",
            "",
            "J'AI, HUISSIER DE JUSTICE SOUSSIGNÉ,",
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
        description="Modèle d'assignation en justice"
    ),
    
    DocumentTemplate(
        id="mise_en_demeure",
        name="Mise en demeure",
        type=TypeDocument.MISE_EN_DEMEURE,
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
            "Malgré mes relances [DÉMARCHES AMIABLES], vous n'avez pas donné suite.",
            "",
            "En conséquence, je vous demande de [ACTION PRÉCISE] dans un délai de [DÉLAI] à compter de la réception de la présente.",
            "",
            "À défaut, je me verrai contraint de saisir les tribunaux compétents pour obtenir :",
            "- [Demande principale]",
            "- [Dommages et intérêts]",
            "- [Frais de procédure]",
            "",
            "Dans l'attente de votre réponse, je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
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
        type=TypeDocument.CONTRAT,
        structure=[
            "CONTRAT DE [TYPE]",
            "",
            "ENTRE LES SOUSSIGNÉS :",
            "",
            "[PARTIE 1], ci-après dénommé « [DÉNOMINATION] »",
            "D'une part,",
            "",
            "ET",
            "",
            "[PARTIE 2], ci-après dénommé « [DÉNOMINATION] »",
            "D'autre part,",
            "",
            "IL A ÉTÉ CONVENU CE QUI SUIT :",
            "",
            "## Article 1 - Objet",
            "[Description de l'objet du contrat]",
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
        type=TypeDocument.MEMOIRE,
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
            "### A. Sur l'irrecevabilité des demandes",
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
            "- Débouter [DEMANDEUR] de l'ensemble de ses demandes",
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
        type=TypeDocument.REQUETE,
        structure=[
            "REQUÊTE AUX FINS DE [OBJET]",
            "",
            "À Monsieur/Madame le Président du [JURIDICTION]",
            "",
            "Le requérant a l'honneur de vous exposer ce qui suit :",
            "",
            "## FAITS",
            "[Exposé des faits]",
            "",
            "## DISCUSSION",
            "[Fondements juridiques]",
            "",
            "## DEMANDE",
            "C'est pourquoi le requérant sollicite qu'il plaise au Tribunal de :",
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
        type=TypeDocument.COURRIER,
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
            "Dans l'attente de vous lire, je vous prie de croire, Cher Confrère, en l'assurance de mes sentiments confraternels dévoués.",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.PEDAGOGIQUE,
        category="Correspondance",
        description="Modèle de courrier entre avocats"
    ),
    
    DocumentTemplate(
        id="note_analyse",
        name="Note d'analyse juridique",
        type=TypeDocument.NOTE,
        structure=[
            "NOTE D'ANALYSE",
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
            "### C. Application au cas d'espèce",
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
            "[Plan d'action]",
            "",
            "[Signature]"
        ],
        style=StyleRedaction.SYNTHETIQUE,
        category="Analyse",
        description="Modèle de note d'analyse juridique interne"
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
        'envoi_pieces': {
            'objet': 'Transmission de pièces - Dossier {reference}',
            'corps': """Maître,
Suite à notre entretien de ce jour, je vous prie de bien vouloir trouver ci-joint les pièces suivantes :
{liste_pieces}
Ces documents viennent compléter le dossier référencé {reference}.
Je reste à votre disposition pour tout complément d'information.
Bien cordialement,
{expediteur}"""
        },
        'demande_informations': {
            'objet': "Demande d'informations complémentaires - {dossier}",
            'corps': """Cher Confrère,
Dans le cadre du dossier {dossier}, j'aurais besoin des informations suivantes :
{liste_questions}
Je vous serais reconnaissant de bien vouloir me faire parvenir ces éléments dans les meilleurs délais.
Bien confraternellement,
{expediteur}"""
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