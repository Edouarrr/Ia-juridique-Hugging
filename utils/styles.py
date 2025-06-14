# utils/styles.py
"""
Styles CSS personnalisés pour l'application juridique
"""

from typing import Dict, Optional

import streamlit as st


def load_custom_css():
    """Charge les styles CSS personnalisés"""
    st.markdown("""
    <style>
    /* ========== VARIABLES CSS ========== */
    :root {
        --primary-color: #1a237e;
        --secondary-color: #283593;
        --success-color: #2e7d32;
        --warning-color: #f57c00;
        --error-color: #c62828;
        --info-color: #0288d1;
        --background-light: #f5f5f5;
        --background-white: #ffffff;
        --text-primary: #212121;
        --text-secondary: #6c757d;
        --border-color: #e0e0e0;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
        --shadow-md: 0 4px 8px rgba(0,0,0,0.1);
        --shadow-lg: 0 8px 16px rgba(0,0,0,0.15);
        --transition-speed: 0.3s;
    }
    
    /* Mode sombre */
    @media (prefers-color-scheme: dark) {
        :root {
            --background-light: #1e1e1e;
            --background-white: #2d2d2d;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --border-color: #404040;
        }
    }
    
    /* ========== BASE ========== */
    .main {
        background-color: var(--background-light);
    }
    
    /* ========== BOUTONS ========== */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all var(--transition-speed) ease;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton > button:hover {
        background-color: var(--secondary-color);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Variantes de boutons */
    .secondary-button > button {
        background-color: var(--secondary-color);
    }
    
    .success-button > button {
        background-color: var(--success-color);
    }
    
    .danger-button > button {
        background-color: var(--error-color);
    }
    
    .warning-button > button {
        background-color: var(--warning-color);
    }
    
    /* ========== CARDS ========== */
    .document-card {
        background: var(--background-white);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        border-left: 5px solid var(--primary-color);
        transition: all var(--transition-speed) ease;
    }
    
    .document-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }
    
    .folder-card {
        background: #e3f2fd;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        border-left: 5px solid var(--secondary-color);
        transition: all var(--transition-speed) ease;
    }
    
    .folder-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }
    
    .info-card {
        background: #e1f5fe;
        border-left: 5px solid var(--info-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .success-card {
        background: #e8f5e9;
        border-left: 5px solid var(--success-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .warning-card {
        background: #fff3e0;
        border-left: 5px solid var(--warning-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .error-card {
        background: #ffebee;
        border-left: 5px solid var(--error-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* ========== SECTIONS ========== */
    .search-section {
        background: var(--background-white);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-sm);
    }
    
    .results-section {
        background: var(--background-white);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
    }
    
    /* ========== NAVIGATION ========== */
    .folder-nav {
        background: var(--background-white);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-sm);
    }
    
    .breadcrumb {
        padding: 0.5rem 0;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    
    .breadcrumb a {
        color: var(--primary-color);
        text-decoration: none;
    }
    
    .breadcrumb a:hover {
        text-decoration: underline;
    }
    
    /* ========== LISTES ========== */
    .search-result {
        background-color: var(--background-white);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        transition: all var(--transition-speed) ease;
    }
    
    .search-result:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--primary-color);
    }
    
    .piece-selectionnee {
        background: #e8f5e9;
        border-left: 3px solid var(--success-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        animation: fadeIn 0.3s ease-out;
    }
    
    /* ========== TIMELINE ========== */
    .timeline-item {
        border-left: 3px solid var(--primary-color);
        padding-left: 1rem;
        margin-left: 0.5rem;
        margin-bottom: 1.5rem;
        position: relative;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 0;
        width: 13px;
        height: 13px;
        border-radius: 50%;
        background-color: var(--primary-color);
        border: 3px solid var(--background-white);
        box-shadow: var(--shadow-sm);
    }
    
    .timeline-item.success::before {
        background-color: var(--success-color);
    }
    
    .timeline-item.warning::before {
        background-color: var(--warning-color);
    }
    
    .timeline-item.error::before {
        background-color: var(--error-color);
    }
    
    /* ========== FORMULAIRES ========== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        border: 1px solid var(--border-color);
        border-radius: 5px;
        transition: border-color var(--transition-speed) ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(26, 35, 126, 0.2);
    }
    
    /* ========== MÉTRICS ========== */
    [data-testid="metric-container"] {
        background-color: var(--background-white);
        border: 1px solid var(--border-color);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: var(--shadow-sm);
        transition: all var(--transition-speed) ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    
    /* ========== EXPANDER ========== */
    .streamlit-expanderHeader {
        background-color: var(--background-light);
        border: 1px solid var(--border-color);
        border-radius: 5px;
        font-weight: 500;
        transition: all var(--transition-speed) ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: var(--background-white);
        border-color: var(--primary-color);
    }
    
    /* ========== TABLEAUX ========== */
    .dataframe {
        border: 1px solid var(--border-color);
        border-radius: 5px;
        overflow: hidden;
    }
    
    .dataframe thead {
        background-color: var(--primary-color);
        color: white;
    }
    
    .dataframe tbody tr:hover {
        background-color: rgba(26, 35, 126, 0.05);
    }
    
    /* ========== BADGES ========== */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 500;
        line-height: 1;
    }
    
    .badge-primary {
        background-color: var(--primary-color);
        color: white;
    }
    
    .badge-success {
        background-color: var(--success-color);
        color: white;
    }
    
    .badge-warning {
        background-color: var(--warning-color);
        color: white;
    }
    
    .badge-error {
        background-color: var(--error-color);
        color: white;
    }
    
    /* ========== ANIMATIONS ========== */
    @keyframes fadeIn {
        from { 
            opacity: 0; 
            transform: translateY(10px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(-20px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    .slide-in {
        animation: slideIn 0.3s ease-out;
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* ========== UTILITAIRES ========== */
    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .text-muted { color: var(--text-secondary); }
    .text-primary { color: var(--primary-color); }
    .text-success { color: var(--success-color); }
    .text-warning { color: var(--warning-color); }
    .text-error { color: var(--error-color); }
    
    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mt-3 { margin-top: 1.5rem; }
    .mb-1 { margin-bottom: 0.5rem; }
    .mb-2 { margin-bottom: 1rem; }
    .mb-3 { margin-bottom: 1.5rem; }
    
    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .stColumn > div {
            margin-bottom: 1rem;
        }
        
        .stButton > button {
            width: 100%;
        }
        
        .document-card,
        .folder-card {
            padding: 1rem;
        }
        
        .search-section {
            padding: 1rem;
        }
    }
    
    /* ========== IMPRESSION ========== */
    @media print {
        .stButton,
        .stTextInput,
        .stSelectbox {
            display: none !important;
        }
        
        .document-card {
            break-inside: avoid;
            box-shadow: none;
            border: 1px solid #000;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def apply_button_style(button_type: str = "primary") -> str:
    """Retourne la classe CSS pour un type de bouton"""
    styles = {
        "primary": "",
        "secondary": "secondary-button",
        "success": "success-button",
        "warning": "warning-button",
        "danger": "danger-button",
        "error": "danger-button"  # Alias
    }
    return styles.get(button_type, "")


def create_card(
    title: str, 
    content: str, 
    icon: str = "", 
    card_type: str = "default"
) -> str:
    """Crée une carte stylisée"""
    card_classes = {
        "default": "document-card",
        "info": "info-card",
        "success": "success-card",
        "warning": "warning-card",
        "error": "error-card"
    }
    
    card_class = card_classes.get(card_type, "document-card")
    
    return f"""
    <div class="{card_class} fade-in">
        <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem; color: var(--primary-color);">
            {icon} {title}
        </div>
        <div>
            {content}
        </div>
    </div>
    """


def create_timeline_item(
    date: str, 
    title: str, 
    description: str,
    status: str = "default"
) -> str:
    """Crée un élément de timeline"""
    status_class = status if status in ["success", "warning", "error"] else ""
    
    return f"""
    <div class="timeline-item {status_class} fade-in">
        <div style="font-weight: 600; color: var(--text-secondary); font-size: 0.9rem;">
            {date}
        </div>
        <div style="font-weight: 600; margin: 0.25rem 0;">
            {title}
        </div>
        <div style="color: var(--text-secondary);">
            {description}
        </div>
    </div>
    """


def create_search_result(
    title: str, 
    content: str, 
    source: str, 
    score: float,
    metadata: Optional[Dict] = None
) -> str:
    """Crée un résultat de recherche stylisé"""
    score_color = (
        "var(--success-color)" if score > 0.8 else 
        "var(--warning-color)" if score > 0.5 else 
        "var(--error-color)"
    )
    
    metadata_html = ""
    if metadata:
        metadata_items = []
        for key, value in metadata.items():
            metadata_items.append(f'<span class="text-muted">{key}: {value}</span>')
        metadata_html = f'<div style="margin-top: 0.5rem;">{" • ".join(metadata_items)}</div>'
    
    return f"""
    <div class="search-result">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <h4 style="margin: 0; color: var(--primary-color);">{title}</h4>
            <span class="badge" style="background-color: {score_color}; color: white;">
                {score:.0%}
            </span>
        </div>
        <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">
            Source: {source}
        </div>
        <div style="color: var(--text-primary);">
            {content[:200]}...
        </div>
        {metadata_html}
    </div>
    """


def create_progress_bar(progress: float, label: str = "") -> str:
    """Crée une barre de progression"""
    color = (
        "var(--success-color)" if progress >= 0.8 else
        "var(--warning-color)" if progress >= 0.5 else
        "var(--primary-color)"
    )
    
    return f"""
    <div style="margin: 1rem 0;">
        {f'<div style="margin-bottom: 0.5rem; font-size: 0.9rem;">{label}</div>' if label else ''}
        <div style="background-color: var(--border-color); border-radius: 5px; overflow: hidden; height: 8px;">
            <div style="background-color: {color}; width: {progress * 100}%; height: 100%; transition: width 0.3s ease;">
            </div>
        </div>
        <div style="text-align: right; margin-top: 0.25rem; font-size: 0.875rem; color: var(--text-secondary);">
            {progress:.0%}
        </div>
    </div>
    """


def create_alert(message: str, alert_type: str = "info", icon: Optional[str] = None) -> str:
    """Crée une alerte stylisée"""
    alert_configs = {
        "info": ("info-card", "ℹ️"),
        "success": ("success-card", "✅"),
        "warning": ("warning-card", "⚠️"),
        "error": ("error-card", "❌")
    }
    
    card_class, default_icon = alert_configs.get(alert_type, ("info-card", "ℹ️"))
    display_icon = icon or default_icon
    
    return f"""
    <div class="{card_class} fade-in">
        {display_icon} {message}
    </div>
    """


def create_breadcrumb(path: List[str]) -> str:
    """Crée un fil d'Ariane stylisé"""
    parts = []
    for i, part in enumerate(path):
        if i < len(path) - 1:
            parts.append(f'<a href="#">{part}</a> >')
        else:
            parts.append(f'<strong>{part}</strong>')
    
    return f'<div class="breadcrumb">{" ".join(parts)}</div>'