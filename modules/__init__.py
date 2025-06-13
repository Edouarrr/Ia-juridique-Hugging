# modules/__init__.py
"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
"""

# Import des dataclasses depuis ce module
try:
    from .dataclasses import *
except ImportError:
    pass

# Configuration MODULE_FUNCTIONS pour chaque module
# Ceci résout le problème "MODULE_FUNCTIONS non trouvé"

# Pour pieces_manager
try:
    from . import pieces_manager
    if not hasattr(pieces_manager, 'MODULE_FUNCTIONS'):
        pieces_manager.MODULE_FUNCTIONS = {
            'display_add_piece': 'Interface pour ajouter une nouvelle pièce',
            'display_piece_detail': 'Afficher les détails d\'une pièce',
            'display_pieces_interface': 'Interface principale de gestion des pièces',
            'display_pieces_list': 'Afficher la liste des pièces',
            'display_pieces_statistics': 'Afficher les statistiques des pièces',
            'display_search_pieces': 'Interface de recherche de pièces'
        }
except ImportError:
    pass

# Pour redaction
try:
    from . import redaction
    if not hasattr(redaction, 'MODULE_FUNCTIONS'):
        redaction.MODULE_FUNCTIONS = {
            'clean_key': 'Nettoyer une clé pour l\'utiliser comme identifiant',
            'create_formatted_docx': 'Créer un document Word formaté',
            'create_letterhead_from_template': 'Créer un en-tête de lettre à partir d\'un template',
            'extract_legal_references': 'Extraire les références juridiques d\'un texte',
            'format_legal_date': 'Formater une date au format juridique français',
            'generate_dynamic_templates': 'Générer des templates dynamiques'
        }
except ImportError:
    pass

# Pour timeline
try:
    from . import timeline
    if not hasattr(timeline, 'MODULE_FUNCTIONS'):
        timeline.MODULE_FUNCTIONS = {
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
except ImportError:
    pass

# Pour recherche
try:
    from . import recherche
    if not hasattr(recherche, 'MODULE_FUNCTIONS'):
        recherche.MODULE_FUNCTIONS = {
            'process_jurisprudence_request': 'Traiter une requête de recherche de jurisprudence',
            'show_jurisprudence_search_interface': 'Afficher l\'interface de recherche de jurisprudence',
            'show_jurisprudence_interface': 'Afficher l\'interface principale de jurisprudence',
            'get_jurisprudence_for_document': 'Obtenir la jurisprudence pour un document',
            'format_jurisprudence_citation': 'Formater une citation de jurisprudence',
            'verify_and_update_citations': 'Vérifier et mettre à jour les citations',
            'search_jurisprudence': 'Rechercher dans la jurisprudence'
        }
except ImportError:
    pass

# Pour dossier_penal
try:
    from . import dossier_penal
    if not hasattr(dossier_penal, 'MODULE_FUNCTIONS'):
        dossier_penal.MODULE_FUNCTIONS = {
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
except ImportError:
    pass

# Pour bordereau
try:
    from . import bordereau
    if not hasattr(bordereau, 'MODULE_FUNCTIONS'):
        bordereau.MODULE_FUNCTIONS = {
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
except ImportError:
    pass

# Pour les autres modules sans erreur, import simple
modules_list = [
    'comparison', 'configuration', 'documents_longs', 'email', 'explorer',
    'import_export', 'jurisprudence', 'mapping', 'plaidoirie',
    'preparation_client', 'redaction_unified', 'selection_pieces',
    'synthesis', 'templates', 'analyse_ia', 'export_juridique',
    'generation_juridique', 'generation_longue', 'integration_juridique',
    'risques'
]

for module_name in modules_list:
    try:
        exec(f"from . import {module_name}")
    except ImportError:
        pass

# Export de tous les modules disponibles
__all__ = [
    'dataclasses',  # Les dataclasses
    'pieces_manager',
    'redaction', 
    'timeline',
    'recherche',
    'dossier_penal',
    'bordereau',
    'comparison',
    'configuration',
    'documents_longs',
    'email',
    'explorer',
    'import_export',
    'jurisprudence',
    'mapping',
    'plaidoirie',
    'preparation_client',
    'redaction_unified',
    'selection_pieces',
    'synthesis',
    'templates',
    'analyse_ia',
    'export_juridique',
    'generation_juridique',
    'generation_longue',
    'integration_juridique',
    'risques'
]