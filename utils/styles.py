# utils/styles.py
"""Styles CSS personnalisés pour l'application"""

import streamlit as st

def load_custom_css():
    """Charge les styles CSS personnalisés"""
    st.markdown("""
    <style>
    :root {
        --primary-color: #1a237e;
        --secondary-color: #283593;
        --success-color: #2e7d32;
        --warning-color: #f57c00;
        --error-color: #c62828;
    }
    
    .main {
        background-color: #f5f5f5;
    }
    
    /* ========== BOUTONS ========== */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--secondary-color);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26, 35, 126, 0.3);
    }
    
    /* ========== CARDS ========== */
    .document-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary-color);
        transition: all 0.3s ease;
    }
    
    .document-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .folder-card {
        background: #e3f2fd;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid var(--secondary-color);
        transition: all 0.3s ease;
    }
    
    .folder-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .folder-nav {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .search-section {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .piece-selectionnee {
        background: #e8f5e9;
        border-left: 3px solid var(--success-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .azure-browser {
        background: #f0f7ff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .style-model {
        background: #fff3e0;
        border-left: 3px solid var(--warning-color);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .letterhead-preview {
        background: white;
        border: 1px solid #ddd;
        padding: 2rem;
        margin: 1rem 0;
        min-height: 400px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* ========== NOUVEAUX STYLES ========== */
    .search-result {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .search-result:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-color: var(--primary-color);
    }
    
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
        border: 3px solid white;
    }
    
    /* Metrics custom */
    [data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Expander amélioré */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        font-weight: 500;
    }
    
    /* ========== ANIMATIONS ========== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .document-card, .folder-card, .piece-selectionnee {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .stColumn > div {
            margin-bottom: 1rem;
        }
        
        .stButton > button {
            width: 100%;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def apply_button_style(button_type: str = "primary"):
    """Retourne la classe CSS pour un type de bouton"""
    styles = {
        "primary": "",
        "secondary": "secondary-button",
        "danger": "danger-button",
        "success": "success-button"
    }
    return styles.get(button_type, "")

def create_card(title: str, content: str, icon: str = ""):
    """Crée une carte stylisée"""
    return f"""
    <div class="document-card fade-in">
        <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem; color: var(--primary-color);">
            {icon} {title}
        </div>
        <div>
            {content}
        </div>
    </div>
    """

def create_timeline_item(date: str, title: str, description: str):
    """Crée un élément de timeline"""
    return f"""
    <div class="timeline-item">
        <div style="font-weight: 600; color: #6c757d; font-size: 0.9rem;">
            {date}
        </div>
        <div style="font-weight: 600; margin: 0.25rem 0;">
            {title}
        </div>
        <div style="color: #6c757d;">
            {description}
        </div>
    </div>
    """

def create_search_result(title: str, content: str, source: str, score: float):
    """Crée un résultat de recherche stylisé"""
    score_color = "var(--success-color)" if score > 0.8 else "var(--warning-color)" if score > 0.5 else "var(--error-color)"
    return f"""
    <div class="search-result">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <h4 style="margin: 0; color: var(--primary-color);">{title}</h4>
            <span style="background-color: {score_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem;">
                {score:.0%}
            </span>
        </div>
        <div style="color: #6c757d; font-size: 0.9rem; margin-bottom: 0.5rem;">
            Source: {source}
        </div>
        <div style="color: #495057;">
            {content[:200]}...
        </div>
    </div>
    """