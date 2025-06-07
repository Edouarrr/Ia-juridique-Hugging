# pages/visualisation.py
"""Page de visualisation et statistiques des analyses juridiques"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
from pyvis.network import Network
import tempfile
import os

from config import TYPES_INFRACTIONS
from utils import load_custom_css, create_section_divider, get_color_scheme

def show():
    """Affiche la page de visualisation"""
    load_custom_css()
    
    st.title("📊 Visualisation et statistiques")
    st.markdown("Analysez vos données juridiques avec des visualisations interactives")
    
    # Vérifier s'il y a des données
    if not st.session_state.get('analyses_count', 0):
        st.info("Aucune donnée disponible. Effectuez d'abord quelques analyses juridiques.")
        show_demo_data()
        return
    
    # Tabs de visualisation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Vue d'ensemble",
        "🎯 Infractions",
        "⚖️ Jurisprudences",
        "📊 Tendances",
        "🔗 Relations"
    ])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_infractions_analysis()
    
    with tab3:
        show_jurisprudence_stats()
    
    with tab4:
        show_trends()
    
    with tab5:
        show_relationships()

def show_overview():
    """Vue d'ensemble des statistiques"""
    st.markdown("### Vue d'ensemble")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        analyses_count = st.session_state.get('analyses_count', 0)
        st.metric(
            "Analyses totales",
            analyses_count,
            delta="+12%" if analyses_count > 10 else None
        )
    
    with col2:
        verifications = st.session_state.get('verifications_count', 0)
        st.metric(
            "Vérifications",
            verifications,
            delta="+8%" if verifications > 5 else None
        )
    
    with col3:
        avg_risk = st.session_state.get('average_risk_score', 5.5)
        st.metric(
            "Risque moyen",
            f"{avg_risk:.1f}/10",
            delta="-0.5" if avg_risk < 6 else "+0.3"
        )
    
    with col4:
        success_rate = 85  # Exemple
        st.metric(
            "Taux de succès",
            f"{success_rate}%",
            delta="+3%"
        )
    
    st.markdown(create_section_divider(), unsafe_allow_html=True)
    
    # Graphiques en colonnes
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution des niveaux de risque
        fig_risk = create_risk_distribution_chart()
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        # Évolution temporelle
        fig_timeline = create_timeline_chart()
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Tableau récapitulatif
    st.markdown("### 📋 Dernières analyses")
    show_recent_analyses_table()

def show_infractions_analysis():
    """Analyse des infractions"""
    st.markdown("### Analyse des infractions")
    
    # Sélecteurs de filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        period = st.selectbox(
            "Période",
            ["30 derniers jours", "3 mois", "6 mois", "1 an", "Tout"]
        )
    
    with col2:
        infraction_filter = st.multiselect(
            "Types d'infractions",
            TYPES_INFRACTIONS,
            default=[]
        )
    
    with col3:
        view_type = st.radio(
            "Type de vue",
            ["Graphique", "Tableau"],
            horizontal=True
        )
    
    # Données d'exemple (à remplacer par les vraies données)
    infraction_data = generate_infraction_data()
    
    if view_type == "Graphique":
        # Graphique en barres horizontales
        fig = px.bar(
            infraction_data,
            x='count',
            y='infraction',
            orientation='h',
            color='severity',
            color_discrete_map={
                'Faible': '#28a745',
                'Modéré': '#ffc107',
                'Élevé': '#fd7e14',
                'Critique': '#dc3545'
            },
            title="Répartition des infractions par type et gravité"
        )
        
        fig.update_layout(
            xaxis_title="Nombre de cas",
            yaxis_title="",
            height=600,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Graphique camembert des catégories
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                infraction_data.groupby('category').sum().reset_index(),
                values='count',
                names='category',
                title="Répartition par catégorie"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Heatmap des corrélations
            fig_heat = create_correlation_heatmap()
            st.plotly_chart(fig_heat, use_container_width=True)
    
    else:
        # Vue tableau
        st.dataframe(
            infraction_data.style.background_gradient(subset=['count']),
            use_container_width=True
        )
        
        # Options d'export
        csv = infraction_data.to_csv(index=False)
        st.download_button(
            "📥 Télécharger CSV",
            csv,
            "infractions_analysis.csv",
            "text/csv"
        )

def show_jurisprudence_stats():
    """Statistiques des jurisprudences"""
    st.markdown("### Analyse des jurisprudences")
    
    # Métriques de vérification
    col1, col2, col3, col4 = st.columns(4)
    
    total_cited = 150  # Exemple
    verified = 120
    unverified = 30
    verification_rate = (verified / total_cited) * 100
    
    with col1:
        st.metric("Total citées", total_cited)
    with col2:
        st.metric("Vérifiées ✅", verified)
    with col3:
        st.metric("Non trouvées ❌", unverified)
    with col4:
        st.metric("Taux de vérification", f"{verification_rate:.1f}%")
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        # Top des juridictions citées
        juridictions_data = pd.DataFrame({
            'Juridiction': ['Cass. crim.', 'Cass. com.', 'CE', 'Cass. civ.', 'CA Paris'],
            'Citations': [45, 35, 28, 22, 20]
        })
        
        fig = px.bar(
            juridictions_data,
            x='Citations',
            y='Juridiction',
            orientation='h',
            title="Juridictions les plus citées"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Évolution temporelle des citations
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
        citations = np.random.randint(10, 30, size=len(dates))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=citations,
            mode='lines+markers',
            name='Citations',
            line=dict(color='#1e3c72', width=3)
        ))
        
        fig.update_layout(
            title="Évolution des citations jurisprudentielles",
            xaxis_title="Mois",
            yaxis_title="Nombre de citations"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Analyse des sources
    st.markdown("#### Sources de vérification")
    
    sources_data = pd.DataFrame({
        'Source': ['Judilibre', 'Légifrance', 'Non trouvé'],
        'Pourcentage': [55, 35, 10]
    })
    
    fig = px.pie(
        sources_data,
        values='Pourcentage',
        names='Source',
        title="Répartition des sources de vérification",
        color_discrete_map={
            'Judilibre': '#1e3c72',
            'Légifrance': '#2a5298',
            'Non trouvé': '#dc3545'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_trends():
    """Affiche les tendances temporelles"""
    st.markdown("### Analyse des tendances")
    
    # Sélecteur de période
    col1, col2 = st.columns([3, 1])
    
    with col1: