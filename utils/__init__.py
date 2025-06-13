# utils/__init__.py
"""
Package utils - Fonctions utilitaires pour l'application juridique
"""

# Import depuis helpers
try:
    from .helpers import (
        init_session_state,
        clean_key,
        generate_document_id,
        analyze_query_intent,
        extract_query_entities,
        extract_intent_details,
        extract_entities,
        extract_dates,
        format_legal_date,
        format_date,
        calculate_text_similarity,
        extract_section,
        chunk_text,
        sanitize_filename,
        format_file_size,
        is_valid_email,
        generate_summary,
        merge_documents,
        extract_legal_references,
        highlight_text,
        create_breadcrumb,
        calculate_read_time,
        get_file_icon,
        format_duration,
        validate_reference,
        extract_monetary_amounts,
        normalize_whitespace,
        truncate_text
    )
    
    __all__ = [
        'init_session_state',
        'clean_key',
        'generate_document_id',
        'analyze_query_intent',
        'extract_query_entities',
        'extract_intent_details',
        'extract_entities',
        'extract_dates',
        'format_legal_date',
        'format_date',
        'calculate_text_similarity',
        'extract_section',
        'chunk_text',
        'sanitize_filename',
        'format_file_size',
        'is_valid_email',
        'generate_summary',
        'merge_documents',
        'extract_legal_references',
        'highlight_text',
        'create_breadcrumb',
        'calculate_read_time',
        'get_file_icon',
        'format_duration',
        'validate_reference',
        'extract_monetary_amounts',
        'normalize_whitespace',
        'truncate_text'
    ]
except ImportError as e:
    print(f"Erreur lors de l'import des helpers: {e}")
    __all__ = []

# Import depuis styles si disponible
try:
    from .styles import *
except ImportError:
    pass

# Import depuis cache_juridique si disponible  
try:
    from .cache_juridique import *
except ImportError:
    pass