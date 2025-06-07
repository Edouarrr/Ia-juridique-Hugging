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
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .document-card, .folder-card, .piece-selectionnee {
            animation: fadeIn 0.3s ease-out;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .stColumn > div {
                margin-bottom: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)