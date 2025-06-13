# modules/__init__.py
"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
"""

# Définition des fonctions disponibles pour chaque module
MODULES_CONFIG = {
    'pieces_manager': {
        'MODULE_FUNCTIONS': {
            'display_add_piece': 'Interface pour ajouter une nouvelle pièce',
            'display_piece_detail': 'Afficher les détails d\'une pièce',
            'display_pieces_interface': 'Interface principale de gestion des pièces',
            'display_pieces_list': 'Afficher la liste des pièces',
            'display_pieces_statistics': 'Afficher les statistiques des pièces',
            'display_search_pieces': 'Interface de recherche de pièces'
        }
    },
    
    'redaction': {
        'MODULE_FUNCTIONS': {
            'clean_key': 'Nettoyer une clé pour l\'utiliser comme identifiant',
            'create_formatted_docx': 'Créer un document Word formaté',
            'create_letterhead_from_template': 'Créer un en-tête de lettre à partir d\'un template',
            'extract_legal_references': 'Extraire les références juridiques d\'un texte',
            'format_legal_date': 'Formater une date au format juridique français',
            'generate_dynamic_templates': 'Générer des templates dynamiques'
        }
    },
    
    'timeline': {
        'MODULE_FUNCTIONS': {
            'analyze_timeline': 'Analyser la chronologie des événements',
            'calculate_event_density': 'Calculer la densité des événements',
            'calculate_event_importance': 'Calculer l\'importance d\'un événement',
            'clean_event_description': 'Nettoyer la description d\'un événement',
            'collect_documents_for_timeline': 'Collecter les documents pour la timeline',
            'create_event_from_context': 'Créer un événement à partir du contexte',
            'create_grouped_timeline': 'Créer une timeline groupée',
            'create_linear_timeline': 'Créer une timeline linéaire',
            'create_timeline_visualization': 'Créer une visualisation de la timeline',
            'detect_timeline_patterns': 'Détecter des patterns dans la timeline',
            'determine_event_category': 'Déterminer la catégorie d\'un événement',
            'display_events_list': 'Afficher la liste des événements',
            'display_timeline_analysis': 'Afficher l\'analyse de la timeline',
            'display_timeline_config_interface': 'Interface de configuration de la timeline',
            'display_timeline_results': 'Afficher les résultats de la timeline',
            'enrich_timeline_with_ai': 'Enrichir la timeline avec l\'IA',
            'export_timeline_to_docx': 'Exporter la timeline en document Word',
            'export_timeline_to_excel': 'Exporter la timeline vers Excel',
            'export_timeline_to_text': 'Exporter la timeline en texte',
            'extract_dates': 'Extraire les dates d\'un texte',
            'extract_entities': 'Extraire les entités d\'un texte',
            'extract_event_keywords': 'Extraire les mots-clés d\'un événement',
            'extract_temporal_events': 'Extraire les événements temporels',
            'extract_timeline_events': 'Extraire les événements de la timeline',
            'filter_timeline_events': 'Filtrer les événements de la timeline',
            'find_activity_peaks': 'Trouver les pics d\'activité',
            'find_recurring_events': 'Trouver les événements récurrents',
            'format_legal_date': 'Formater une date au format juridique',
            'generate_timeline': 'Générer une timeline',
            'make_subplots': 'Créer des sous-graphiques',
            'parse_ai_timeline_response': 'Parser la réponse IA de la timeline',
            'prepare_timeline_data': 'Préparer les données de la timeline',
            'process_timeline_request': 'Traiter une requête de timeline',
            'show_timeline_statistics': 'Afficher les statistiques de la timeline'
        }
    },
    
    'recherche': {
        'MODULE_FUNCTIONS': {
            'process_jurisprudence_request': 'Traiter une requête de recherche de jurisprudence',
            'show_jurisprudence_search_interface': 'Afficher l\'interface de recherche de jurisprudence',
            'show_jurisprudence_interface': 'Afficher l\'interface principale de jurisprudence',
            'get_jurisprudence_for_document': 'Obtenir la jurisprudence pour un document',
            'format_jurisprudence_citation': 'Formater une citation de jurisprudence',
            'verify_and_update_citations': 'Vérifier et mettre à jour les citations',
            'search_jurisprudence': 'Rechercher dans la jurisprudence'
        }
    },
    
    'dossier_penal': {
        'MODULE_FUNCTIONS': {
            'display_analyse': 'Afficher l\'analyse du dossier pénal',
            'display_chronologie': 'Afficher la chronologie du dossier',
            'display_dashboard': 'Afficher le tableau de bord',
            'display_dossier_detail': 'Afficher les détails du dossier',
            'display_dossier_penal_interface': 'Interface principale du dossier pénal',
            'display_general_info': 'Afficher les informations générales',
            'display_new_dossier_form': 'Formulaire de nouveau dossier',
            'display_parties': 'Afficher les parties du dossier',
            'display_pieces': 'Afficher les pièces du dossier'
        }
    },
    
    'bordereau': {
        'MODULE_FUNCTIONS': {
            'create_bordereau': 'Créer un nouveau bordereau',
            'create_bordereau_docx': 'Créer un bordereau au format Word',
            'create_bordereau_txt': 'Créer un bordereau au format texte',
            'create_bordereau_xlsx': 'Créer un bordereau au format Excel',
            'display_bordereau_interface': 'Interface principale des bordereaux',
            'display_pieces_table': 'Afficher le tableau des pièces',
            'generate_bordereau_summary': 'Générer un résumé du bordereau',
            'process_bordereau_request': 'Traiter une requête de bordereau',
            'validate_bordereau': 'Valider un bordereau'
        }
    },
    
    'email': {
        'MODULE_FUNCTIONS': {
            'display_email_interface': 'Interface principale des emails',
            'send_email_with_attachments': 'Envoyer un email avec pièces jointes',
            'create_email_template': 'Créer un template d\'email',
            'prepare_email_content': 'Préparer le contenu de l\'email',
            'validate_email_addresses': 'Valider les adresses email'
        }
    },
    
    'documents_longs': {
        'MODULE_FUNCTIONS': {
            'display_documents_longs_interface': 'Interface des documents longs',
            'generate_long_document': 'Générer un document long',
            'analyze_document_structure': 'Analyser la structure du document',
            'create_document_outline': 'Créer le plan du document',
            'export_long_document': 'Exporter le document long'
        }
    },
    
    'mapping': {
        'MODULE_FUNCTIONS': {
            'display_mapping_interface': 'Interface de mapping',
            'create_document_mapping': 'Créer un mapping de documents',
            'visualize_relationships': 'Visualiser les relations',
            'export_mapping_data': 'Exporter les données de mapping'
        }
    },
    
    'plaidoirie': {
        'MODULE_FUNCTIONS': {
            'display_plaidoirie_interface': 'Interface de plaidoirie',
            'generate_plaidoirie_structure': 'Générer la structure de plaidoirie',
            'create_argument_points': 'Créer les points d\'argumentation',
            'export_plaidoirie_notes': 'Exporter les notes de plaidoirie'
        }
    },
    
    'preparation_client': {
        'MODULE_FUNCTIONS': {
            'display_preparation_client_interface': 'Interface de préparation client',
            'create_client_summary': 'Créer un résumé pour le client',
            'prepare_meeting_agenda': 'Préparer l\'agenda de réunion',
            'generate_client_report': 'Générer un rapport client'
        }
    },
    
    'synthesis': {
        'MODULE_FUNCTIONS': {
            'display_synthesis_interface': 'Interface de synthèse',
            'generate_case_synthesis': 'Générer une synthèse du dossier',
            'create_executive_summary': 'Créer un résumé exécutif',
            'analyze_key_points': 'Analyser les points clés'
        }
    },
    
    'templates': {
        'MODULE_FUNCTIONS': {
            'display_templates_interface': 'Interface des templates',
            'create_new_template': 'Créer un nouveau template',
            'edit_template': 'Éditer un template',
            'apply_template': 'Appliquer un template',
            'manage_template_library': 'Gérer la bibliothèque de templates'
        }
    },
    
    'selection_pieces': {
        'MODULE_FUNCTIONS': {
            'display_selection_pieces_interface': 'Interface de sélection des pièces',
            'filter_pieces_by_criteria': 'Filtrer les pièces par critères',
            'create_piece_selection': 'Créer une sélection de pièces',
            'export_selected_pieces': 'Exporter les pièces sélectionnées'
        }
    },
    
    'jurisprudence': {
        'MODULE_FUNCTIONS': {
            'display_jurisprudence_interface': 'Interface de jurisprudence',
            'search_jurisprudence_database': 'Rechercher dans la base de jurisprudence',
            'analyze_jurisprudence_trends': 'Analyser les tendances jurisprudentielles',
            'export_jurisprudence_report': 'Exporter un rapport de jurisprudence'
        }
    },
    
    'import_export': {
        'MODULE_FUNCTIONS': {
            'display_import_export_interface': 'Interface d\'import/export',
            'import_documents': 'Importer des documents',
            'export_dossier': 'Exporter un dossier',
            'validate_import_format': 'Valider le format d\'import'
        }
    },
    
    'explorer': {
        'MODULE_FUNCTIONS': {
            'display_explorer_interface': 'Interface d\'exploration',
            'browse_dossier_structure': 'Parcourir la structure du dossier',
            'search_in_dossier': 'Rechercher dans le dossier',
            'preview_document': 'Prévisualiser un document'
        }
    },
    
    'configuration': {
        'MODULE_FUNCTIONS': {
            'display_configuration_interface': 'Interface de configuration',
            'save_configuration': 'Sauvegarder la configuration',
            'load_configuration': 'Charger la configuration',
            'reset_to_defaults': 'Réinitialiser aux valeurs par défaut'
        }
    },
    
    'comparison': {
        'MODULE_FUNCTIONS': {
            'display_comparison_interface': 'Interface de comparaison',
            'compare_documents': 'Comparer des documents',
            'highlight_differences': 'Mettre en évidence les différences',
            'generate_comparison_report': 'Générer un rapport de comparaison'
        }
    },
    
    'redaction_unified': {
        'MODULE_FUNCTIONS': {
            'display_unified_redaction_interface': 'Interface de rédaction unifiée',
            'create_unified_document': 'Créer un document unifié',
            'merge_document_sections': 'Fusionner les sections de documents',
            'apply_unified_formatting': 'Appliquer un formatage unifié'
        }
    },
    
    'risques': {
        'MODULE_FUNCTIONS': {
            'display_risques_interface': 'Interface de gestion des risques',
            'analyze_case_risks': 'Analyser les risques du dossier',
            'create_risk_matrix': 'Créer une matrice des risques',
            'generate_risk_report': 'Générer un rapport de risques'
        }
    },
    
    'analyse_ia': {
        'MODULE_FUNCTIONS': {
            'display_analyse_ia_interface': 'Interface d\'analyse IA',
            'analyze_with_ai': 'Analyser avec l\'IA',
            'generate_ai_insights': 'Générer des insights IA',
            'export_ai_analysis': 'Exporter l\'analyse IA'
        }
    },
    
    'export_juridique': {
        'MODULE_FUNCTIONS': {
            'display_export_juridique_interface': 'Interface d\'export juridique',
            'export_legal_format': 'Exporter au format juridique',
            'create_legal_bundle': 'Créer un bundle juridique',
            'validate_legal_export': 'Valider l\'export juridique'
        }
    },
    
    'generation_juridique': {
        'MODULE_FUNCTIONS': {
            'display_generation_juridique_interface': 'Interface de génération juridique',
            'generate_legal_document': 'Générer un document juridique',
            'apply_legal_templates': 'Appliquer des templates juridiques',
            'validate_generated_content': 'Valider le contenu généré'
        }
    },
    
    'generation_longue': {
        'MODULE_FUNCTIONS': {
            'display_generation_longue_interface': 'Interface de génération longue',
            'generate_extended_document': 'Générer un document étendu',
            'manage_long_generation': 'Gérer la génération longue',
            'monitor_generation_progress': 'Surveiller la progression'
        }
    },
    
    'integration_juridique': {
        'MODULE_FUNCTIONS': {
            'display_integration_juridique_interface': 'Interface d\'intégration juridique',
            'integrate_legal_sources': 'Intégrer les sources juridiques',
            'sync_legal_databases': 'Synchroniser les bases juridiques',
            'validate_integrations': 'Valider les intégrations'
        }
    }
}

# Fonction helper pour obtenir MODULE_FUNCTIONS d'un module
def get_module_functions(module_name: str) -> dict:
    """Retourne le dictionnaire MODULE_FUNCTIONS pour un module donné"""
    if module_name in MODULES_CONFIG:
        return MODULES_CONFIG[module_name]['MODULE_FUNCTIONS']
    return {}

# Import dynamique des modules
imported_modules = {}

# Tentative d'import de chaque module
for module_name in MODULES_CONFIG.keys():
    try:
        module = __import__(f'modules.{module_name}', fromlist=['*'])
        imported_modules[module_name] = module
        
        # Injecter MODULE_FUNCTIONS dans le module s'il n'existe pas
        if not hasattr(module, 'MODULE_FUNCTIONS'):
            setattr(module, 'MODULE_FUNCTIONS', MODULES_CONFIG[module_name]['MODULE_FUNCTIONS'])
    except ImportError as e:
        print(f"Module {module_name} non trouvé ou erreur d'import: {e}")
        # Créer un module factice avec MODULE_FUNCTIONS
        class DummyModule:
            pass
        dummy = DummyModule()
        dummy.MODULE_FUNCTIONS = MODULES_CONFIG[module_name]['MODULE_FUNCTIONS']
        imported_modules[module_name] = dummy

# Export des modules importés
for name, module in imported_modules.items():
    globals()[name] = module

# Liste des modules disponibles
AVAILABLE_MODULES = list(MODULES_CONFIG.keys())

# Export
__all__ = ['MODULES_CONFIG', 'get_module_functions', 'AVAILABLE_MODULES'] + list(imported_modules.keys())