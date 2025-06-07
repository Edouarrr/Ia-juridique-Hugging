# utils/__init__.py
from .helpers import (
    format_date,
    format_currency,
    sanitize_text,
    extract_numbers,
    calculate_risk_score,
    generate_unique_id,
    validate_email,
    validate_phone,
    clean_html,
    truncate_text,
    highlight_text,
    create_summary
)

from .styles import (
    load_custom_css,
    get_custom_styles,
    apply_theme,
    get_color_scheme,
    format_metric_card,
    create_gradient_background
)

# Export explicite
__all__ = [
    # Helpers
    'format_date',
    'format_currency',
    'sanitize_text',
    'extract_numbers',
    'calculate_risk_score',
    'generate_unique_id',
    'validate_email',
    'validate_phone',
    'clean_html',
    'truncate_text',
    'highlight_text',
    'create_summary',
    # Styles
    'load_custom_css',
    'get_custom_styles',
    'apply_theme',
    'get_color_scheme',
    'format_metric_card',
    'create_gradient_background'
]