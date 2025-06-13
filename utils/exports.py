# utils/exports.py
"""
Exports simplifiés pour faciliter l'import des fonctions utils les plus courantes

Usage:
    from utils.exports import *
    
Ou pour des imports spécifiques:
    from utils.exports import (
        format_legal_date,
        extract_entities,
        validate_siren,
        cache_result
    )
"""

# ========== SESSION ==========
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
    set_user_preference
)

# ========== TEXT PROCESSING ==========
from .text_processing import (
    clean_key,
    normalize_whitespace,
    truncate_text,
    extract_section,
    chunk_text,
    calculate_text_similarity,
    highlight_text,
    extract_key_phrases,
    generate_summary,
    calculate_read_time,
    extract_entities,
    extract_monetary_amounts,
    clean_legal_text,
    format_legal_citations
)

# ========== DATE TIME ==========
from .date_time import (
    format_date,
    format_legal_date,
    format_date_juridique,  # Alias
    format_duration,
    extract_dates,
    parse_date,
    is_business_day,
    get_next_business_day,
    calculate_business_days,
    add_business_days,
    format_relative_date
)

# ========== DOCUMENT UTILS ==========
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

# ========== LEGAL UTILS ==========
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

# ========== FILE UTILS ==========
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
    is_valid_email
)

# ========== CACHE MANAGER ==========
from .cache_manager import (
    CacheJuridique,
    get_cache,
    cache_result,
    cache_streamlit,
    CacheActesJuridiques,
    show_cache_management
)

# ========== FORMATTERS ==========
from .formatters import (
    create_letterhead_from_template,
    create_formatted_docx,
    format_party_designation,
    apply_legal_numbering,
    create_document_header,
    create_table_of_contents,
    split_into_pages,
    add_page_numbers,
    format_legal_list,
    format_signature_block,
    format_annex_reference,
    create_document_footer
)

# ========== STYLES ==========
from .styles import (
    load_custom_css,
    apply_button_style,
    create_card,
    create_timeline_item,
    create_search_result,
    create_progress_bar,
    create_alert
)

# ========== VALIDATORS ==========
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

# ========== CONSTANTS ==========
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

# ========== LISTE COMPLETE DES EXPORTS ==========
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
    
    # Text Processing
    'clean_key',
    'normalize_whitespace',
    'truncate_text',
    'extract_section',
    'chunk_text',
    'calculate_text_similarity',
    'highlight_text',
    'extract_key_phrases',
    'generate_summary',
    'calculate_read_time',
    'extract_entities',
    'extract_monetary_amounts',
    'clean_legal_text',
    'format_legal_citations',
    
    # Date Time
    'format_date',
    'format_legal_date',
    'format_date_juridique',
    'format_duration',
    'extract_dates',
    'parse_date',
    'is_business_day',
    'get_next_business_day',
    'calculate_business_days',
    'add_business_days',
    'format_relative_date',
    
    # Document Utils
    'generate_document_id',
    'merge_documents',
    'split_document',
    'extract_document_metadata',
    'create_document_index',
    'compare_documents',
    'create_document_summary',
    'get_document_statistics',
    'create_breadcrumb',
    
    # Legal Utils
    'extract_legal_references',
    'analyze_query_intent',
    'extract_query_entities',
    'extract_intent_details',
    'extract_legal_terms',
    'format_legal_amount',
    'validate_reference',
    'categorize_legal_document',
    'extract_parties',
    'highlight_legal_terms',
    
    # File Utils
    'sanitize_filename',
    'format_file_size',
    'get_file_icon',
    'get_file_extension',
    'is_valid_filename',
    'get_mime_type',
    'is_text_file',
    'is_document_file',
    'is_image_file',
    'create_unique_filename',
    'organize_files_by_type',
    'is_valid_email',
    
    # Cache Manager
    'CacheJuridique',
    'get_cache',
    'cache_result',
    'cache_streamlit',
    'CacheActesJuridiques',
    'show_cache_management',
    
    # Formatters
    'create_letterhead_from_template',
    'create_formatted_docx',
    'format_party_designation',
    'apply_legal_numbering',
    'create_document_header',
    'create_table_of_contents',
    'split_into_pages',
    'add_page_numbers',
    'format_legal_list',
    'format_signature_block',
    'format_annex_reference',
    'create_document_footer',
    
    # Styles
    'load_custom_css',
    'apply_button_style',
    'create_card',
    'create_timeline_item',
    'create_search_result',
    'create_progress_bar',
    'create_alert',
    
    # Validators
    'validate_siren',
    'validate_siret',
    'validate_iban',
    'validate_phone_number',
    'validate_postal_code',
    'validate_legal_form',
    'validate_case_number',
    'validate_infraction_code',
    'validate_lawyer_bar_number',
    'validate_document_reference',
    'validate_date_range',
    'validate_amount',
    'validate_percentage',
    'validate_juridiction_name',
    'validate_fields',
    
    # Constants
    'DOCUMENT_TYPES',
    'PHASES_PROCEDURE',
    'JURIDICTIONS',
    'INFRACTIONS_COURANTES',
    'FORMES_JURIDIQUES',
    'QUALITES_PARTIES',
    'BARREAUX',
    'CURRENCIES',
    'LIMITS',
    'ACCEPTED_FILE_TYPES',
    'ERROR_MESSAGES',
    'REGEX_PATTERNS',
    'ICONS',
    'COLORS',
    'DEPARTEMENTS'
]