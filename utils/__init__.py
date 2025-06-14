# utils/__init__.py
"""
Package utils - Fonctions utilitaires pour l'application juridique
"""

# Import des fonctions principales de chaque module

# Session
from .session import (
    initialize_session_state,
    get_session_value,
    set_session_value,
    update_session_values,
    clear_session_results,
    add_to_history,
    toggle_favorite,
    is_favorite,
    get_user_preference,
    set_user_preference,
    reset_session
)

# Text Processing
from .text_processing import (
    clean_text,
    process_text,
    fix_punctuation,
    normalize_quotes,
    extract_sentences,
    extract_paragraphs,
    count_words,
    extract_keywords,
    highlight_text,
    remove_html_tags,
    normalize_whitespace,
    split_into_chunks
)

# Date Time
from .date_time import (
    format_date,
    format_legal_date,
    format_date_juridique,
    format_duration,
    extract_dates,
    parse_date,
    get_date_range,
    is_business_day,
    get_next_business_day,
    calculate_business_days,
    add_business_days,
    format_relative_date,
    get_quarter,
    get_week_number,
    MOIS_FR,
    JOURS_FR,
    MONTHS_FR
)

# Document Utils
from .document_utils import (
    generate_document_id,
    merge_documents,
    split_document,
    extract_document_metadata,
    create_document_index,
    compare_documents,
    create_document_summary,
    get_document_statistics,
    create_breadcrumb
)

# Legal Utils
from .legal_utils import (
    extract_legal_references,
    analyze_query_intent,
    extract_query_entities,
    extract_intent_details,
    extract_legal_terms,
    format_legal_amount,
    validate_reference,
    categorize_legal_document,
    extract_parties,
    highlight_legal_terms
)

# File Utils
from .file_utils import (
    sanitize_filename,
    format_file_size,
    get_file_icon,
    get_file_extension,
    is_valid_filename,
    get_mime_type,
    is_text_file,
    is_document_file,
    is_image_file,
    create_unique_filename,
    organize_files_by_type,
    get_file_info,
    split_path,
    is_valid_email
)

# Cache Manager
from .cache_manager import (
    CacheJuridique,
    get_cache,
    cache_result,
    cache_streamlit,
    CacheActesJuridiques,
    show_cache_management,
    CACHE_DIR,
    CACHE_DURATION
)

# Formatters
from .formatters import (
    format_date as format_date_formatter,  # Éviter le conflit avec date_time
    format_date_long,
    format_datetime,
    format_currency,
    format_percentage,
    format_phone,
    format_case_number,
    format_name,
    format_address,
    format_duration as format_duration_formatter,  # Éviter le conflit
    format_file_path,
    format_list_items,
    format_legal_reference
)

# Styles
from .styles import (
    load_custom_css,
    apply_button_style,
    create_card,
    create_timeline_item,
    create_search_result,
    create_progress_bar,
    create_alert,
    create_breadcrumb as create_breadcrumb_styled  # Éviter le conflit
)

# Validators
from .validators import (
    validate_siren,
    validate_siret,
    validate_iban,
    validate_phone_number,
    validate_postal_code,
    validate_legal_form,
    validate_case_number,
    validate_infraction_code,
    validate_lawyer_bar_number,
    validate_document_reference,
    validate_date_range,
    validate_amount,
    validate_percentage,
    validate_juridiction_name,
    validate_fields
)

# Constants
from .constants import (
    DOCUMENT_TYPES,
    PHASES_PROCEDURE,
    JURIDICTIONS,
    INFRACTIONS_COURANTES,
    FORMES_JURIDIQUES,
    QUALITES_PARTIES,
    BARREAUX,
    CURRENCIES,
    LIMITS,
    ACCEPTED_FILE_TYPES,
    ERROR_MESSAGES,
    REGEX_PATTERNS,
    ICONS,
    COLORS,
    DEPARTEMENTS
)

# Helper functions from helpers.py (si ce fichier existe)
from .helpers import (
    truncate_text,
    clean_key,
    generate_unique_id,
    extract_date_from_filename,
    normalize_document_type,
    calculate_document_hash,
    parse_search_query,
    estimate_reading_time,
    generate_document_summary,
    validate_container_name,
    merge_document_metadata,
    format_error_message,
    create_error_report
)

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
    
    # Legal Utils
    'extract_legal_references',
    'analyze_query_intent',
    'format_legal_amount',
    
    # File Utils
    'sanitize_filename',
    'format_file_size',
    'is_valid_email',
    
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
    
    # Version
    '__version__'
]