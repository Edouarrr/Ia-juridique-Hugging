# utils/styles.py
"""Styles et thèmes pour l'application Streamlit"""

import streamlit as st
from typing import Dict, Optional, Tuple

def load_custom_css():
    """Charge les styles CSS personnalisés pour l'application"""
    css = """
    <style>
    /* Styles globaux */
    .main {
        padding-top: 2rem;
    }
    
    /* En-tête personnalisé */
    .custom-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Cartes métriques */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3c72;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Alertes personnalisées */
    .custom-alert {
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .alert-success {
        background-color: #d4edda;
        border-left-color: #28a745;
        color: #155724;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border-left-color: #ffc107;
        color: #856404;
    }
    
    .alert-danger {
        background-color: #f8d7da;
        border-left-color: #dc3545;
        color: #721c24;
    }
    
    .alert-info {
        background-color: #d1ecf1;
        border-left-color: #17a2b8;
        color: #0c5460;
    }
    
    /* Jurisprudence vérifiée */
    .jurisprudence-verified {
        background-color: #d4edda;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #28a745;
    }
    
    .jurisprudence-unverified {
        background-color: #f8d7da;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #dc3545;
        text-decoration: line-through;
        opacity: 0.7;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.875rem;
        font-weight: 600;
        border-radius: 15px;
        margin: 0.25rem;
    }
    
    .badge-primary {
        background-color: #007bff;
        color: white;
    }
    
    .badge-success {
        background-color: #28a745;
        color: white;
    }
    
    .badge-warning {
        background-color: #ffc107;
        color: #212529;
    }
    
    .badge-danger {
        background-color: #dc3545;
        color: white;
    }
    
    /* Tableaux améliorés */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        overflow: hidden;
    }
    
    .custom-table th {
        background-color: #f8f9fa;
        padding: 1rem;
        text-align: left;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #dee2e6;
    }
    
    .custom-table td {
        padding: 1rem;
        border-bottom: 1px solid #dee2e6;
    }
    
    .custom-table tr:hover {
        background-color: #f8f9fa;
    }
    
    /* Boutons personnalisés */
    .custom-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .custom-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Sections */
    .section-divider {
        height: 2px;
        background: linear-gradient(to right, #667eea, #764ba2);
        margin: 2rem 0;
        border-radius: 1px;
    }
    
    /* Highlight de texte */
    .highlight {
        background-color: #ffeb3b;
        padding: 0.1rem 0.3rem;
        border-radius: 3px;
        font-weight: 500;
    }
    
    /* Progress bars */
    .progress-container {
        background-color: #e9ecef;
        border-radius: 10px;
        padding: 3px;
        margin: 1rem 0;
    }
    
    .progress-bar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        height: 20px;
        border-radius: 8px;
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 2px solid #e9ecef;
    }
    
    section[data-testid="stSidebar"] .element-container {
        margin-bottom: 1rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .metric-card {
            margin-bottom: 1rem;
        }
        
        .custom-header {
            padding: 1rem;
        }
        
        .metric-value {
            font-size: 2rem;
        }
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def get_custom_styles() -> Dict[str, str]:
    """Retourne un dictionnaire de styles personnalisés"""
    return {
        "primary_color": "#1e3c72",
        "secondary_color": "#2a5298",
        "success_color": "#28a745",
        "warning_color": "#ffc107",
        "danger_color": "#dc3545",
        "info_color": "#17a2b8",
        "background_color": "#f8f9fa",
        "text_color": "#212529",
        "border_radius": "8px",
        "box_shadow": "0 2px 4px rgba(0, 0, 0, 0.1)"
    }

def apply_theme(theme_name: str = "default"):
    """Applique un thème à l'application"""
    themes = {
        "default": {
            "primaryColor": "#1e3c72",
            "backgroundColor": "#ffffff",
            "secondaryBackgroundColor": "#f8f9fa",
            "textColor": "#212529"
        },
        "dark": {
            "primaryColor": "#667eea",
            "backgroundColor": "#1a1a1a",
            "secondaryBackgroundColor": "#2d2d2d",
            "textColor": "#ffffff"
        },
        "professional": {
            "primaryColor": "#2c3e50",
            "backgroundColor": "#ecf0f1",
            "secondaryBackgroundColor": "#bdc3c7",
            "textColor": "#2c3e50"
        }
    }
    
    theme = themes.get(theme_name, themes["default"])
    
    # Appliquer le thème via CSS
    css = f"""
    <style>
    .stApp {{
        background-color: {theme['backgroundColor']};
        color: {theme['textColor']};
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def get_color_scheme(risk_level: str) -> Tuple[str, str]:
    """Retourne un schéma de couleur selon le niveau de risque"""
    schemes = {
        "Faible": ("#28a745", "#d4edda"),
        "Modéré": ("#ffc107", "#fff3cd"),
        "Élevé": ("#fd7e14", "#ffe5d0"),
        "Critique": ("#dc3545", "#f8d7da")
    }
    
    return schemes.get(risk_level, ("#6c757d", "#e9ecef"))

def format_metric_card(label: str, value: str, delta: Optional[str] = None, color: str = "primary") -> str:
    """Crée une carte métrique formatée en HTML"""
    color_map = {
        "primary": "#1e3c72",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#17a2b8"
    }
    
    card_color = color_map.get(color, color_map["primary"])
    
    delta_html = ""
    if delta:
        delta_color = "#28a745" if delta.startswith("+") else "#dc3545"
        delta_html = f'<div style="color: {delta_color}; font-size: 1rem;">{delta}</div>'
    
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {card_color};">{value}</div>
        {delta_html}
    </div>
    """

def create_gradient_background(start_color: str, end_color: str, direction: str = "135deg") -> str:
    """Crée un style de fond en dégradé"""
    return f"background: linear-gradient({direction}, {start_color} 0%, {end_color} 100%);"

def create_alert_box(message: str, alert_type: str = "info") -> str:
    """Crée une boîte d'alerte personnalisée"""
    icons = {
        "success": "✅",
        "warning": "⚠️",
        "danger": "❌",
        "info": "ℹ️"
    }
    
    icon = icons.get(alert_type, "ℹ️")
    
    return f"""
    <div class="custom-alert alert-{alert_type}">
        <strong>{icon}</strong> {message}
    </div>
    """

def create_progress_bar(value: int, max_value: int = 100, label: str = "") -> str:
    """Crée une barre de progression personnalisée"""
    percentage = min(100, max(0, (value / max_value) * 100))
    
    return f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {percentage}%;">
            {label if label else f"{percentage:.0f}%"}
        </div>
    </div>
    """

def create_badge(text: str, badge_type: str = "primary") -> str:
    """Crée un badge personnalisé"""
    return f'<span class="badge badge-{badge_type}">{text}</span>'

def highlight_jurisprudence(text: str, verified: bool = True) -> str:
    """Formate une jurisprudence selon son statut de vérification"""
    css_class = "jurisprudence-verified" if verified else "jurisprudence-unverified"
    icon = "✅" if verified else "❌"
    
    return f'<div class="{css_class}">{icon} {text}</div>'

def create_header(title: str, subtitle: Optional[str] = None) -> str:
    """Crée un en-tête personnalisé"""
    subtitle_html = f"<p style='font-size: 1.2rem; margin-top: 0.5rem;'>{subtitle}</p>" if subtitle else ""
    
    return f"""
    <div class="custom-header fade-in">
        <h1 style='margin: 0;'>{title}</h1>
        {subtitle_html}
    </div>
    """

def create_section_divider() -> str:
    """Crée un séparateur de section"""
    return '<div class="section-divider"></div>'

# Export
__all__ = [
    'load_custom_css',
    'get_custom_styles',
    'apply_theme',
    'get_color_scheme',
    'format_metric_card',
    'create_gradient_background',
    'create_alert_box',
    'create_progress_bar',
    'create_badge',
    'highlight_jurisprudence',
    'create_header',
    'create_section_divider'
]