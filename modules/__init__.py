# modules/__init__.py
"""
Package modules - Contient tous les modules fonctionnels de l'application juridique
"""

# Import des dataclasses depuis ce module
try:
    from .dataclasses import *
except ImportError:
    pass

# Configuration MODULE_FUNCTIONS pour TOUS les modules

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

# Pour plaidoirie.py (basé sur votre vrai fichier)
try:
    from . import plaidoirie
    if not hasattr(plaidoirie, 'MODULE_FUNCTIONS'):
        plaidoirie.MODULE_FUNCTIONS = {
            'process_plaidoirie_request': 'Traite une demande de génération de plaidoirie',
            'display_plaidoirie_config_interface': 'Interface de configuration pour la plaidoirie',
            'generate_plaidoirie': 'Génère une plaidoirie complète',
            'build_plaidoirie_prompt': 'Construit le prompt pour générer la plaidoirie',
            'build_plaidoirie_system_prompt': 'Construit le prompt système pour la plaidoirie',
            'get_available_documents_for_plaidoirie': 'Récupère les documents disponibles pour la plaidoirie',
            'detect_document_type': 'Détecte le type d\'un document pour la plaidoirie',
            'extract_key_points': 'Extrait les points clés de la plaidoirie',
            'extract_plaidoirie_structure': 'Extrait la structure hiérarchique de la plaidoirie',
            'extract_oral_markers': 'Extrait les marqueurs pour l\'oral',
            'display_plaidoirie_results': 'Affiche les résultats de la plaidoirie',
            'display_plaidoirie_text': 'Affiche le texte de la plaidoirie avec mise en forme',
            'show_rehearsal_mode': 'Mode répétition pour la plaidoirie',
            'create_speaker_version': 'Crée une version annotée pour l\'orateur',
            'export_plaidoirie_to_pdf': 'Exporte la plaidoirie en PDF',
            'show_plaidoirie_statistics': 'Affiche les statistiques de la plaidoirie',
            'create_plaidoirie_mindmap': 'Crée une carte mentale de la plaidoirie'
        }
except ImportError:
    pass

# Pour mapping.py (basé sur votre vrai fichier)
try:
    from . import mapping
    if not hasattr(mapping, 'MODULE_FUNCTIONS'):
        mapping.MODULE_FUNCTIONS = {
            'process_mapping_request': 'Traite une demande de cartographie des relations',
            'collect_documents_for_mapping': 'Collecte les documents pour la cartographie',
            'display_mapping_config_interface': 'Interface de configuration pour la cartographie',
            'generate_relationship_mapping': 'Génère la cartographie des relations',
            'extract_entities_and_relationships': 'Extrait les entités et relations des documents',
            'extract_document_entities': 'Extrait les entités d\'un document',
            'extract_document_relationships': 'Extrait les relations d\'un document',
            'get_relation_patterns': 'Retourne les patterns de relations selon le type de mapping',
            'extract_entities_from_match': 'Extrait les entités source et cible d\'un match de pattern',
            'extract_proximity_relationships': 'Extrait les relations basées sur la proximité dans le texte',
            'calculate_relationship_strength': 'Calcule la force d\'une relation',
            'consolidate_relationships': 'Consolide les relations dupliquées',
            'enrich_with_ai_analysis': 'Enrichit l\'analyse avec l\'IA',
            'parse_ai_mapping_response': 'Parse la réponse de l\'IA pour extraire entités et relations',
            'merge_entities': 'Fusionne les listes d\'entités',
            'filter_mapping_data': 'Filtre les données selon la configuration',
            'analyze_network': 'Analyse le réseau avec NetworkX',
            'basic_network_analysis': 'Analyse basique du réseau sans NetworkX',
            'create_network_visualization': 'Crée la visualisation du réseau avec Plotly',
            'calculate_node_positions': 'Calcule les positions des nœuds selon le layout',
            'create_edge_trace': 'Crée le trace des arêtes pour Plotly',
            'create_node_trace': 'Crée le trace des nœuds pour Plotly',
            'display_mapping_results': 'Affiche les résultats de la cartographie',
            'display_network_analysis': 'Affiche l\'analyse du réseau',
            'display_entities_list': 'Affiche la liste des entités',
            'display_relationships_list': 'Affiche la liste des relations',
            'display_mapping_statistics': 'Affiche les statistiques détaillées de la cartographie',
            'generate_mapping_report': 'Génère un rapport textuel de la cartographie',
            'export_mapping_to_excel': 'Exporte la cartographie vers Excel',
            'show_advanced_network_analysis': 'Affiche l\'analyse réseau avancée'
        }
except ImportError:
    pass

# Pour email.py (basé sur votre vrai fichier)
try:
    from . import email
    if not hasattr(email, 'MODULE_FUNCTIONS'):
        email.MODULE_FUNCTIONS = {
            'process_email_request': 'Traite une demande d\'envoi par email',
            'extract_email_recipients': 'Extrait les destinataires depuis la requête',
            'create_email_config': 'Crée la configuration de l\'email',
            'determine_email_subject': 'Détermine l\'objet de l\'email selon le contexte',
            'generate_email_body': 'Génère le corps de l\'email selon le contexte',
            'show_email_configuration': 'Interface de configuration de l\'email',
            'prepare_email_content_and_attachments': 'Prépare le contenu et les pièces jointes',
            'get_available_attachments': 'Récupère les documents disponibles pour attachement',
            'prepare_attachment': 'Prépare une pièce jointe dans le format demandé',
            'create_pdf_attachment': 'Crée une pièce jointe PDF',
            'create_docx_attachment': 'Crée une pièce jointe DOCX',
            'show_email_preview': 'Affiche un aperçu de l\'email',
            'send_email_with_progress': 'Envoie l\'email avec barre de progression',
            'get_smtp_configuration': 'Récupère la configuration SMTP',
            'create_mime_message': 'Crée le message MIME complet',
            'show_smtp_configuration_help': 'Affiche l\'aide pour la configuration SMTP',
            'save_email_draft': 'Sauvegarde un brouillon d\'email',
            'save_email_history': 'Sauvegarde l\'historique des emails envoyés',
            'log_email_sent': 'Enregistre l\'envoi dans les logs',
            'show_email_interface': 'Interface principale de gestion des emails',
            'show_email_drafts': 'Affiche les brouillons d\'emails',
            'show_email_history': 'Affiche l\'historique des emails envoyés',
            'export_email_history': 'Exporte l\'historique des emails',
            'show_email_configuration_interface': 'Interface de configuration des emails',
            'test_smtp_connection': 'Teste la connexion SMTP',
            'get_default_email_templates': 'Retourne les templates d\'emails par défaut',
            'get_default_signatures': 'Retourne les signatures par défaut',
            'prepare_and_send_document': 'Prépare et envoie un document par email'
        }
except ImportError:
    pass

# Pour preparation_client.py (basé sur votre vrai fichier)
try:
    from . import preparation_client
    if not hasattr(preparation_client, 'MODULE_FUNCTIONS'):
        preparation_client.MODULE_FUNCTIONS = {
            'process_preparation_client_request': 'Traite une demande de préparation client',
            'display_preparation_config_interface': 'Interface de configuration pour la préparation',
            'generate_client_preparation': 'Génère une préparation complète pour le client',
            'build_preparation_prompt': 'Construit le prompt pour la préparation',
            'build_preparation_system_prompt': 'Construit le prompt système pour la préparation',
            'extract_key_qa': 'Extrait les questions-réponses clés',
            'extract_never_say': 'Extrait les choses à ne jamais dire',
            'extract_preparation_exercises': 'Extrait les exercices de préparation',
            'detect_exercise_type': 'Détecte le type d\'exercice',
            'estimate_preparation_duration': 'Estime la durée de préparation nécessaire',
            'display_preparation_results': 'Affiche les résultats de la préparation',
            'display_full_preparation': 'Affiche le document complet de préparation',
            'display_qa_section': 'Affiche la section questions/réponses',
            'display_never_say_section': 'Affiche la section des choses à ne jamais dire',
            'categorize_never_say': 'Catégorise les phrases à éviter',
            'get_danger_explanation': 'Explique pourquoi une phrase est dangereuse',
            'display_exercises_section': 'Affiche la section des exercices',
            'display_preparation_summary': 'Affiche une fiche résumé de la préparation',
            'create_preparation_summary': 'Crée une fiche résumé de la préparation',
            'create_print_friendly_summary': 'Crée une version imprimable de la fiche résumé',
            'highlight_search_terms': 'Surligne les termes recherchés dans le contenu',
            'show_interrogation_simulation': 'Mode simulation d\'interrogatoire',
            'display_simulation_results': 'Affiche les résultats de la simulation',
            'create_simulation_report': 'Crée un rapport détaillé de la simulation',
            'show_exercise_timer': 'Timer pour les exercices de préparation',
            'show_exercise_practice': 'Interface de pratique pour un exercice',
            'create_mobile_version': 'Crée une version mobile de la préparation',
            'export_preparation_to_pdf': 'Exporte la préparation en PDF'
        }
except ImportError:
    pass

# Pour synthesis.py (basé sur votre vrai fichier)
try:
    from . import synthesis
    if not hasattr(synthesis, 'MODULE_FUNCTIONS'):
        synthesis.MODULE_FUNCTIONS = {
            'process_synthesis_request': 'Traite une demande de synthèse',
            'synthesize_selected_pieces': 'Synthétise les pièces sélectionnées',
            'synthesize_documents': 'Synthétise une liste de documents',
            'synthesize_search_results': 'Synthétise des résultats de recherche',
            'construct_synthesis_context': 'Construit le contexte pour la synthèse',
            'display_synthesis_interface': 'Affiche l\'interface de synthèse',
            'extract_sections_from_synthesis': 'Extrait les sections d\'une synthèse',
            'extract_key_points_from_synthesis': 'Extrait les points clés d\'une synthèse',
            'export_synthesis_to_docx': 'Exporte la synthèse en format Word',
            'show_synthesis_statistics': 'Affiche les statistiques de la synthèse',
            'determine_document_category': 'Détermine la catégorie d\'un document',
            'search_documents_by_reference': 'Recherche des documents par référence'
        }
except ImportError:
    pass

# Pour templates.py (basé sur votre vrai fichier)
try:
    from . import templates
    if not hasattr(templates, 'MODULE_FUNCTIONS'):
        templates.MODULE_FUNCTIONS = {
            'process_template_request': 'Traite une demande liée aux templates',
            'detect_template_action': 'Détecte l\'action demandée sur les templates',
            'show_templates_interface': 'Interface principale des templates',
            'show_templates_library': 'Affiche la bibliothèque de templates',
            'get_all_templates': 'Récupère tous les templates disponibles',
            'get_template_categories': 'Récupère les catégories uniques',
            'get_template_types': 'Récupère les types uniques',
            'filter_templates': 'Filtre les templates',
            'show_template_card': 'Affiche une carte de template',
            'show_template_preview': 'Affiche un aperçu du template',
            'show_create_template_interface': 'Interface de création de template',
            'show_template_creation_preview': 'Aperçu du template en création',
            'create_new_template': 'Crée un nouveau template',
            'show_edit_template_interface': 'Interface d\'édition de template',
            'update_template': 'Met à jour un template existant',
            'show_apply_template_interface': 'Interface d\'application de template',
            'get_variable_default_value': 'Obtient une valeur par défaut pour une variable',
            'generate_document_from_template': 'Génère un document depuis un template',
            'enrich_with_ai': 'Enrichit le contenu avec l\'IA',
            'add_relevant_jurisprudence': 'Ajoute la jurisprudence pertinente au document',
            'extract_legal_keywords': 'Extrait les mots-clés juridiques d\'un contenu',
            'show_templates_configuration': 'Configuration des templates',
            'confirm_delete_template': 'Demande confirmation pour supprimer un template',
            'delete_template': 'Supprime un template',
            'save_templates_to_storage': 'Sauvegarde les templates',
            'load_templates_from_storage': 'Charge les templates depuis le stockage',
            'export_all_templates': 'Exporte tous les templates',
            'import_templates': 'Importe des templates depuis un fichier',
            'apply_template': 'Applique un template sélectionné',
            'get_template_by_type': 'Récupère un template par type de document',
            'get_template_structure': 'Récupère la structure d\'un template par nom',
            'create_template_from_document': 'Crée un template à partir d\'un document existant'
        }
except ImportError:
    pass

# Pour les autres modules (définitions de base)
# comparison
try:
    from . import comparison
    if not hasattr(comparison, 'MODULE_FUNCTIONS'):
        comparison.MODULE_FUNCTIONS = {
            'display_comparison_interface': 'Interface de comparaison',
            'compare_documents': 'Comparer des documents',
            'highlight_differences': 'Mettre en évidence les différences',
            'generate_comparison_report': 'Générer un rapport de comparaison'
        }
except ImportError:
    pass

# configuration
try:
    from . import configuration
    if not hasattr(configuration, 'MODULE_FUNCTIONS'):
        configuration.MODULE_FUNCTIONS = {
            'display_configuration_interface': 'Interface de configuration',
            'save_configuration': 'Sauvegarder la configuration',
            'load_configuration': 'Charger la configuration',
            'reset_to_defaults': 'Réinitialiser aux valeurs par défaut'
        }
except ImportError:
    pass

# documents_longs
try:
    from . import documents_longs
    if not hasattr(documents_longs, 'MODULE_FUNCTIONS'):
        documents_longs.MODULE_FUNCTIONS = {
            'display_documents_longs_interface': 'Interface des documents longs',
            'generate_long_document': 'Générer un document long',
            'analyze_document_structure': 'Analyser la structure du document',
            'create_document_outline': 'Créer le plan du document',
            'export_long_document': 'Exporter le document long'
        }
except ImportError:
    pass

# explorer
try:
    from . import explorer
    if not hasattr(explorer, 'MODULE_FUNCTIONS'):
        explorer.MODULE_FUNCTIONS = {
            'display_explorer_interface': 'Interface d\'exploration',
            'browse_dossier_structure': 'Parcourir la structure du dossier',
            'search_in_dossier': 'Rechercher dans le dossier',
            'preview_document': 'Prévisualiser un document'
        }
except ImportError:
    pass

# import_export
try:
    from . import import_export
    if not hasattr(import_export, 'MODULE_FUNCTIONS'):
        import_export.MODULE_FUNCTIONS = {
            'display_import_export_interface': 'Interface d\'import/export',
            'import_documents': 'Importer des documents',
            'export_dossier': 'Exporter un dossier',
            'validate_import_format': 'Valider le format d\'import'
        }
except ImportError:
    pass

# jurisprudence
try:
    from . import jurisprudence
    if not hasattr(jurisprudence, 'MODULE_FUNCTIONS'):
        jurisprudence.MODULE_FUNCTIONS = {
            'display_jurisprudence_interface': 'Interface de jurisprudence',
            'search_jurisprudence_database': 'Rechercher dans la base de jurisprudence',
            'analyze_jurisprudence_trends': 'Analyser les tendances jurisprudentielles',
            'export_jurisprudence_report': 'Exporter un rapport de jurisprudence'
        }
except ImportError:
    pass

# selection_pieces
try:
    from . import selection_pieces
    if not hasattr(selection_pieces, 'MODULE_FUNCTIONS'):
        selection_pieces.MODULE_FUNCTIONS = {
            'display_selection_pieces_interface': 'Interface de sélection des pièces',
            'filter_pieces_by_criteria': 'Filtrer les pièces par critères',
            'create_piece_selection': 'Créer une sélection de pièces',
            'export_selected_pieces': 'Exporter les pièces sélectionnées'
        }
except ImportError:
    pass

# redaction_unified
try:
    from . import redaction_unified
    if not hasattr(redaction_unified, 'MODULE_FUNCTIONS'):
        redaction_unified.MODULE_FUNCTIONS = {
            'display_unified_redaction_interface': 'Interface de rédaction unifiée',
            'create_unified_document': 'Créer un document unifié',
            'merge_document_sections': 'Fusionner les sections de documents',
            'apply_unified_formatting': 'Appliquer un formatage unifié'
        }
except ImportError:
    pass

# risques
try:
    from . import risques
    if not hasattr(risques, 'MODULE_FUNCTIONS'):
        risques.MODULE_FUNCTIONS = {
            'display_risques_interface': 'Interface de gestion des risques',
            'analyze_case_risks': 'Analyser les risques du dossier',
            'create_risk_matrix': 'Créer une matrice des risques',
            'generate_risk_report': 'Générer un rapport de risques'
        }
except ImportError:
    pass

# analyse_ia
try:
    from . import analyse_ia
    if not hasattr(analyse_ia, 'MODULE_FUNCTIONS'):
        analyse_ia.MODULE_FUNCTIONS = {
            'display_analyse_ia_interface': 'Interface d\'analyse IA',
            'analyze_with_ai': 'Analyser avec l\'IA',
            'generate_ai_insights': 'Générer des insights IA',
            'export_ai_analysis': 'Exporter l\'analyse IA'
        }
except ImportError:
    pass

# export_juridique
try:
    from . import export_juridique
    if not hasattr(export_juridique, 'MODULE_FUNCTIONS'):
        export_juridique.MODULE_FUNCTIONS = {
            'display_export_juridique_interface': 'Interface d\'export juridique',
            'export_legal_format': 'Exporter au format juridique',
            'create_legal_bundle': 'Créer un bundle juridique',
            'validate_legal_export': 'Valider l\'export juridique'
        }
except ImportError:
    pass

# generation_juridique
try:
    from . import generation_juridique
    if not hasattr(generation_juridique, 'MODULE_FUNCTIONS'):
        generation_juridique.MODULE_FUNCTIONS = {
            'display_generation_juridique_interface': 'Interface de génération juridique',
            'generate_legal_document': 'Générer un document juridique',
            'apply_legal_templates': 'Appliquer des templates juridiques',
            'validate_generated_content': 'Valider le contenu généré'
        }
except ImportError:
    pass

# generation_longue
try:
    from . import generation_longue
    if not hasattr(generation_longue, 'MODULE_FUNCTIONS'):
        generation_longue.MODULE_FUNCTIONS = {
            'display_generation_longue_interface': 'Interface de génération longue',
            'generate_extended_document': 'Générer un document étendu',
            'manage_long_generation': 'Gérer la génération longue',
            'monitor_generation_progress': 'Surveiller la progression'
        }
except ImportError:
    pass

# integration_juridique
try:
    from . import integration_juridique
    if not hasattr(integration_juridique, 'MODULE_FUNCTIONS'):
        integration_juridique.MODULE_FUNCTIONS = {
            'display_integration_juridique_interface': 'Interface d\'intégration juridique',
            'integrate_legal_sources': 'Intégrer les sources juridiques',
            'sync_legal_databases': 'Synchroniser les bases juridiques',
            'validate_integrations': 'Valider les intégrations'
        }
except ImportError:
    pass

# Export de tous les modules disponibles
__all__ = [
    'dataclasses',
    'pieces_manager',
    'redaction',
    'timeline',
    'recherche',
    'dossier_penal',
    'bordereau',
    'plaidoirie',
    'mapping',
    'email',
    'preparation_client',
    'synthesis',
    'templates',
    'comparison',
    'configuration',
    'documents_longs',
    'explorer',
    'import_export',
    'jurisprudence',
    'selection_pieces',
    'redaction_unified',
    'risques',
    'analyse_ia',
    'export_juridique',
    'generation_juridique',
    'generation_longue',
    'integration_juridique'
]