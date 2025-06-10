# models/configurations.py
"""Configurations pour les templates de génération de documents"""

from typing import Dict, List, Any
import json
from modules.dataclasses import StyleConfig

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
    
    "moderne": StyleConfig(
        name="Moderne simplifié",
        formality_level="moderne",
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
        formality_level="moderne",
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
        'moderne': {
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
        return cls.STYLES_REDACTION.get(style_name, cls.STYLES_REDACTION['moderne'])