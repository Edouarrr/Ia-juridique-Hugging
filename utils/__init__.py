# utils/__init__.py
"""
Package utils - Fonctions utilitaires pour l'application juridique
"""

# Import des fonctions principales de chaque module

# Cache Manager (peut dépendre de Streamlit)
try:
    from .cache_manager import (CACHE_DIR, CACHE_DURATION, CacheActesJuridiques,
                                CacheJuridique, cache_result, cache_streamlit,
                                get_cache, show_cache_management)
except Exception:  # Ignore si dépendance manquante
    CACHE_DIR = CACHE_DURATION = None
    CacheActesJuridiques = CacheJuridique = None
    cache_result = cache_streamlit = lambda *args, **kwargs: None
    get_cache = show_cache_management = lambda *args, **kwargs: None
# Constants
from .constants import (ACCEPTED_FILE_TYPES, BARREAUX, COLORS, CURRENCIES,
                        DEPARTEMENTS, DOCUMENT_TYPES, ERROR_MESSAGES,
                        FORMES_JURIDIQUES, ICONS, INFRACTIONS_COURANTES,
                        JURIDICTIONS, LIMITS, PHASES_PROCEDURE,
                        QUALITES_PARTIES, REGEX_PATTERNS,
                        LEGAL_SUGGESTIONS)
# Date Time
from .date_time import (JOURS_FR, MOIS_FR, MONTHS_FR, add_business_days,
                        calculate_business_days, extract_dates, format_date,
                        format_date_juridique, format_duration,
                        format_legal_date, format_relative_date,
                        get_date_range, get_next_business_day, get_quarter,
                        get_week_number, is_business_day, parse_date)
# Document Utils
from .document_utils import (compare_documents, create_breadcrumb,
                             create_document_index, create_document_summary,
                             extract_document_metadata, generate_document_id,
                             get_document_statistics, merge_documents,
                             split_document)
# File Utils
from .file_utils import (
    create_unique_filename,
    format_file_size,
    get_file_extension,
    get_file_icon,
    get_file_info,
    get_mime_type,
    is_document_file,
    is_image_file,
    is_text_file,
    is_valid_email,
    validate_uploaded_file,
    is_valid_filename,
    organize_files_by_type,
    sanitize_filename,
    clean_filename,
    split_path,
    ATTACHMENT_MIME_TYPES,
    EmailConfig,
)
# Formatters
from .formatters import format_address, format_case_number, format_currency
from .formatters import \
    format_date as format_date_formatter  # Éviter le conflit avec date_time
from .formatters import format_date_long, format_datetime
from .formatters import \
    format_duration as format_duration_formatter  # Éviter le conflit
from .formatters import (format_file_path, format_legal_reference,
                         format_list_items, format_name, format_percentage,
                         format_phone)
from .formatters import (
    _to_roman,
    apply_legal_numbering,
    format_legal_list,
    format_signature_block,
    format_annex_reference,
    create_document_footer,
    create_document_header,
    create_table_of_contents,
    split_into_pages,
    add_page_numbers,
    format_party_designation,
    create_letterhead_from_template,
    create_formatted_docx,
)
# Helper functions from helpers.py (si ce fichier existe)
from .helpers import (calculate_document_hash, clean_key, create_error_report,
                      estimate_reading_time, extract_date_from_filename,
                      format_error_message, generate_document_summary,
                      generate_unique_id, merge_document_metadata,
                      normalize_document_type, parse_search_query,
                      truncate_text, validate_container_name)
# Legal Utils
from .legal_utils import (analyze_query_intent, categorize_legal_document,
                          extract_intent_details, extract_legal_references,
                          extract_legal_terms, extract_parties,
                          extract_query_entities, format_legal_amount,
                          highlight_legal_terms, validate_reference)
# Session (peut dépendre de Streamlit)
try:
    from .session import (
        add_to_history,
        clear_session_results,
        get_session_value,
        get_user_preference,
        initialize_session_state,
        is_favorite,
        log_module_usage,
        log_search,
        reset_session,
        set_dossier_summary,
        set_session_value,
        set_user_preference,
        toggle_favorite,
        update_session_values,
    )
except Exception:
    add_to_history = clear_session_results = get_session_value = lambda *a, **k: None
    get_user_preference = initialize_session_state = lambda *a, **k: None
    is_favorite = reset_session = set_session_value = lambda *a, **k: None
    set_user_preference = toggle_favorite = update_session_values = lambda *a, **k: None
    log_search = log_module_usage = set_dossier_summary = lambda *a, **k: None

# Styles (peut dépendre de Streamlit)
try:
    from .styles import apply_button_style, create_alert
    from .styles import \
        create_breadcrumb as create_breadcrumb_styled  # Éviter le conflit
    from .styles import (create_card, create_progress_bar, create_search_result,
                         create_timeline_item, load_custom_css)
except Exception:
    apply_button_style = create_alert = lambda *a, **k: None
    create_breadcrumb_styled = create_card = create_progress_bar = lambda *a, **k: None
    create_search_result = create_timeline_item = load_custom_css = lambda *a, **k: None
# Text Processing
from .text_processing import (clean_text, count_words, extract_keywords,
                              extract_paragraphs, extract_sentences,
                              fix_punctuation, highlight_text,
                              normalize_quotes, normalize_whitespace,
                              process_text, remove_html_tags,
                              split_into_chunks)
# Validators
from .validators import (validate_amount, validate_case_number,
                         validate_date_range, validate_document_reference,
                         validate_fields, validate_iban,
                         validate_infraction_code, validate_juridiction_name,
                         validate_lawyer_bar_number, validate_legal_form,
                         validate_percentage, validate_phone_number,
                         validate_postal_code, validate_siren, validate_siret)

# Alias pour compatibilité
init_session_state = initialize_session_state

# Version
__version__ = "1.0.0"

# All exports
__all__ = [
    # Session
    'initialize_session_state',
    'get_session_value',
    'set_session_value',
    'update_session_values',
    'clear_session_results',
    'add_to_history',
    'log_search',
    'log_module_usage',
    'set_dossier_summary',
    'toggle_favorite',
    'is_favorite',
    'get_user_preference',
    'set_user_preference',
    'reset_session',
    'init_session_state',
    
    # Text Processing
    'clean_text',
    'process_text',
    'normalize_whitespace',
    'truncate_text',
    'clean_key',
    
    # Date Time
    'format_date',
    'format_legal_date',
    'format_date_juridique',
    'format_duration',
    
    # Document Utils
    'generate_document_id',
    'merge_documents',
    'split_document',

    # Formatters
    '_to_roman',
    'apply_legal_numbering',
    'format_legal_list',
    'format_signature_block',
    'format_annex_reference',
    'create_document_footer',
    'create_document_header',
    'create_table_of_contents',
    'split_into_pages',
    'add_page_numbers',
    'format_party_designation',
    'create_letterhead_from_template',
    'create_formatted_docx',

    # Legal Utils
    'extract_legal_references',
    'analyze_query_intent',
    'format_legal_amount',
    
    # File Utils
    'sanitize_filename',
    'clean_filename',
    'format_file_size',
    'is_valid_email',
    'validate_uploaded_file',
    'EmailConfig',
    'ATTACHMENT_MIME_TYPES',
    
    # Cache Manager
    'CacheJuridique',
    'get_cache',
    'cache_result',
    
    # Styles
    'load_custom_css',
    
    # Validators
    'validate_siren',
    'validate_siret',
    'validate_phone_number',
    
    # Constants
    'DOCUMENT_TYPES',
    'JURIDICTIONS',
    'ICONS',
    'LEGAL_SUGGESTIONS',

    # Version
    '__version__'
]
