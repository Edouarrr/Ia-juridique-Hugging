# utils/styles.py
"""Styles et composants visuels personnalisés"""

import streamlit as st

def load_custom_css():
    """Charge les styles CSS personnalisés"""
    st.markdown("""
    <style>
    /* Styles principaux */
    .main-header {
        background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f5f5f5;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .search-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .document-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        transition: all 0.2s;
    }
    
    .document-card:hover {
        border-color: #1a237e;
        box-shadow: 0 2px 8px rgba(26, 35, 126, 0.1);
    }
    
    .folder-card {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #bbdefb;
        margin-bottom: 0.5rem;
    }
    
    .folder-nav {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-info {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .alert-success {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    
    .alert-warning {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    
    .alert-error {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    
    /* Boutons personnalisés */
    .stButton > button {
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Sidebar personnalisée */
    .css-1d391kg {
        background-color: #f5f5f5;
    }
    
    /* Amélioration des métriques */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Tables */
    .dataframe {
        font-size: 14px;
    }
    
    .dataframe thead th {
        background-color: #1a237e !important;
        color: white !important;
    }
    
    /* Expanders personnalisés */
    .streamlit-expanderHeader {
        background-color: #f5f5f5;
        border-radius: 8px;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background-color: #1a237e;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1a237e;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)


def create_header(title: str, subtitle: str = "", level: int = 1):
    """Crée un en-tête stylisé
    
    Args:
        title: Titre principal
        subtitle: Sous-titre optionnel
        level: Niveau du titre (1-6)
    """
    header_tag = f"h{level}" if 1 <= level <= 6 else "h1"
    
    if subtitle:
        return f"""
        <div class="main-header">
            <{header_tag}>{title}</{header_tag}>
            <p style='font-size: 1.2rem; margin-top: 0.5rem;'>{subtitle}</p>
        </div>
        """
    else:
        return f"""
        <div style='margin-bottom: 1rem;'>
            <{header_tag} style='color: #1a237e;'>{title}</{header_tag}>
        </div>
        """


def format_metric_card(title: str, value: str, delta: str = None, color: str = "primary"):
    """Formate une carte de métrique"""
    colors = {
        "primary": "#1a237e",
        "success": "#4caf50",
        "warning": "#ff9800",
        "danger": "#f44336",
        "info": "#2196f3"
    }
    
    card_color = colors.get(color, colors["primary"])
    
    delta_html = ""
    if delta:
        delta_color = "#4caf50" if delta.startswith("+") else "#f44336"
        delta_html = f"<p style='color: {delta_color}; font-size: 0.9rem; margin: 0;'>{delta}</p>"
    
    return f"""
    <div class="metric-card" style="border-left: 4px solid {card_color};">
        <h4 style='color: {card_color}; margin: 0;'>{title}</h4>
        <p style='font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;'>{value}</p>
        {delta_html}
    </div>
    """


def create_alert_box(message: str, alert_type: str = "info"):
    """Crée une boîte d'alerte stylisée"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    icon = icons.get(alert_type, "ℹ️")
    
    return f"""
    <div class="alert-box alert-{alert_type}">
        <span style='font-size: 1.2rem; margin-right: 0.5rem;'>{icon}</span>
        {message}
    </div>
    """


def create_progress_bar(progress: float, text: str = ""):
    """Crée une barre de progression personnalisée"""
    percentage = int(progress * 100)
    
    return f"""
    <div style='margin: 1rem 0;'>
        {f"<p style='margin-bottom: 0.5rem;'>{text}</p>" if text else ""}
        <div style='background-color: #e0e0e0; border-radius: 10px; overflow: hidden;'>
            <div style='background-color: #1a237e; width: {percentage}%; padding: 0.5rem; color: white; text-align: center;'>
                {percentage}%
            </div>
        </div>
    </div>
    """


def create_section_divider(title: str = ""):
    """Crée un séparateur de section stylisé"""
    if title:
        return f"""
        <div style='margin: 2rem 0; text-align: center;'>
            <div style='display: flex; align-items: center;'>
                <div style='flex: 1; height: 1px; background-color: #e0e0e0;'></div>
                <div style='padding: 0 1rem; color: #666; font-weight: 500;'>{title}</div>
                <div style='flex: 1; height: 1px; background-color: #e0e0e0;'></div>
            </div>
        </div>
        """
    else:
        return "<hr style='margin: 2rem 0; border: none; border-top: 1px solid #e0e0e0;'>"


def format_legal_reference(reference: str, type_ref: str = "article"):
    """Formate une référence juridique"""
    colors = {
        "article": "#1976d2",
        "jurisprudence": "#388e3c",
        "doctrine": "#7b1fa2"
    }
    
    color = colors.get(type_ref, "#333")
    
    return f"""
    <span style='
        background-color: {color}15;
        color: {color};
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.9rem;
    '>{reference}</span>
    """


def create_card_grid(cards: list, columns: int = 3):
    """Crée une grille de cartes"""
    grid_html = "<div style='display: grid; grid-template-columns: repeat({}, 1fr); gap: 1rem;'>".format(columns)
    
    for card in cards:
        grid_html += f"""
        <div class="document-card">
            <h4 style='color: #1a237e; margin-top: 0;'>{card.get('title', '')}</h4>
            <p style='color: #666; margin: 0.5rem 0;'>{card.get('subtitle', '')}</p>
            <p>{card.get('content', '')}</p>
        </div>
        """
    
    grid_html += "</div>"
    return grid_html