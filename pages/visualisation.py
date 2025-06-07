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
        date_range = st.date_input(
            "Période d'analyse",
            value=[datetime.now() - timedelta(days=180), datetime.now()],
            key="trends_date_range"
        )
    
    with col2:
        granularity = st.selectbox(
            "Granularité",
            ["Jour", "Semaine", "Mois"],
            index=2
        )
    
    # Graphique multi-lignes des tendances
    fig = create_trends_chart(date_range, granularity)
    st.plotly_chart(fig, use_container_width=True)
    
    # Analyse prédictive
    st.markdown("#### 🔮 Analyse prédictive")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Prédiction du volume
        st.info("""
        **Prévisions pour les 30 prochains jours :**
        - Volume d'analyses : +15% attendu
        - Infractions dominantes : Corruption, ABS
        - Niveau de risque moyen : Stable (5.5/10)
        """)
    
    with col2:
        # Recommandations
        st.success("""
        **Recommandations :**
        - Renforcer la veille sur la corruption
        - Former les équipes sur les nouvelles jurisprudences
        - Mettre à jour les procédures de compliance
        """)
    
    # Saisonnalité
    st.markdown("#### 📅 Analyse de saisonnalité")
    
    months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    seasonality_data = np.random.randint(50, 150, size=12)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months,
        y=seasonality_data,
        marker_color=['#1e3c72' if i < 6 else '#2a5298' for i in range(12)]
    ))
    
    fig.update_layout(
        title="Saisonnalité des analyses (année en cours)",
        xaxis_title="Mois",
        yaxis_title="Nombre d'analyses"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_relationships():
    """Visualisation des relations entre entités"""
    st.markdown("### Analyse des relations")
    
    # Type de relation à visualiser
    relation_type = st.selectbox(
        "Type de relation",
        ["Infractions connexes", "Personnes impliquées", "Jurisprudences liées", "Réseau complet"]
    )
    
    # Créer le graphe
    if relation_type == "Infractions connexes":
        show_infractions_network()
    elif relation_type == "Personnes impliquées":
        show_persons_network()
    elif relation_type == "Jurisprudences liées":
        show_jurisprudence_network()
    else:
        show_complete_network()
    
    # Statistiques du réseau
    st.markdown("#### 📊 Statistiques du réseau")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nœuds", "48")
    with col2:
        st.metric("Connexions", "127")
    with col3:
        st.metric("Densité", "0.24")
    with col4:
        st.metric("Composantes", "3")

# Fonctions de création de graphiques

def create_risk_distribution_chart():
    """Crée le graphique de distribution des risques"""
    risk_levels = ['Faible', 'Modéré', 'Élevé', 'Critique']
    counts = [15, 35, 25, 10]
    colors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
    
    fig = go.Figure(data=[
        go.Bar(
            x=risk_levels,
            y=counts,
            marker_color=colors
        )
    ])
    
    fig.update_layout(
        title="Distribution des niveaux de risque",
        xaxis_title="Niveau de risque",
        yaxis_title="Nombre d'analyses",
        showlegend=False
    )
    
    return fig

def create_timeline_chart():
    """Crée le graphique d'évolution temporelle"""
    dates = pd.date_range(start='2024-06-01', end='2024-12-31', freq='W')
    analyses = np.cumsum(np.random.randint(2, 8, size=len(dates)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=analyses,
        mode='lines+markers',
        name='Analyses cumulées',
        line=dict(color='#1e3c72', width=3),
        fill='tozeroy',
        fillcolor='rgba(30, 60, 114, 0.2)'
    ))
    
    fig.update_layout(
        title="Évolution du nombre d'analyses",
        xaxis_title="Date",
        yaxis_title="Nombre cumulé",
        hovermode='x unified'
    )
    
    return fig

def generate_infraction_data():
    """Génère des données d'exemple pour les infractions"""
    infractions = []
    categories = ['Financier', 'Social', 'Commercial', 'Fiscal']
    severities = ['Faible', 'Modéré', 'Élevé', 'Critique']
    
    for inf in TYPES_INFRACTIONS[:10]:
        infractions.append({
            'infraction': inf,
            'count': np.random.randint(5, 50),
            'category': np.random.choice(categories),
            'severity': np.random.choice(severities, p=[0.2, 0.4, 0.3, 0.1])
        })
    
    return pd.DataFrame(infractions)

def create_correlation_heatmap():
    """Crée une heatmap de corrélation"""
    infractions = TYPES_INFRACTIONS[:8]
    correlation_matrix = np.random.rand(8, 8)
    correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
    np.fill_diagonal(correlation_matrix, 1)
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix,
        x=infractions,
        y=infractions,
        colorscale='Blues',
        text=np.round(correlation_matrix, 2),
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title="Corrélations entre infractions",
        height=400
    )
    
    return fig

def create_trends_chart(date_range, granularity):
    """Crée le graphique des tendances"""
    # Générer des dates selon la granularité
    if granularity == "Jour":
        dates = pd.date_range(start=date_range[0], end=date_range[1], freq='D')
    elif granularity == "Semaine":
        dates = pd.date_range(start=date_range[0], end=date_range[1], freq='W')
    else:
        dates = pd.date_range(start=date_range[0], end=date_range[1], freq='M')
    
    # Données simulées
    analyses = np.random.randint(5, 20, size=len(dates))
    verifications = np.random.randint(10, 30, size=len(dates))
    risk_scores = 5 + np.random.randn(len(dates)) * 0.5
    
    fig = go.Figure()
    
    # Analyses
    fig.add_trace(go.Scatter(
        x=dates,
        y=analyses,
        mode='lines+markers',
        name='Analyses',
        yaxis='y'
    ))
    
    # Vérifications
    fig.add_trace(go.Scatter(
        x=dates,
        y=verifications,
        mode='lines+markers',
        name='Vérifications',
        yaxis='y'
    ))
    
    # Score de risque
    fig.add_trace(go.Scatter(
        x=dates,
        y=risk_scores,
        mode='lines',
        name='Score de risque',
        yaxis='y2',
        line=dict(dash='dash')
    ))
    
    fig.update_layout(
        title="Évolution des indicateurs clés",
        xaxis_title="Date",
        yaxis=dict(title="Nombre", side='left'),
        yaxis2=dict(title="Score de risque", overlaying='y', side='right', range=[0, 10]),
        hovermode='x unified',
        height=500
    )
    
    return fig

def show_recent_analyses_table():
    """Affiche un tableau des analyses récentes"""
    # Données d'exemple
    data = []
    for i in range(5):
        data.append({
            'Date': (datetime.now() - timedelta(days=i*3)).strftime('%d/%m/%Y'),
            'Type': np.random.choice(TYPES_INFRACTIONS[:5]),
            'Risque': np.random.choice(['Faible', 'Modéré', 'Élevé', 'Critique']),
            'Jurisprudences': np.random.randint(3, 12),
            'Statut': np.random.choice(['✅ Complété', '⏳ En cours', '📋 Brouillon'])
        })
    
    df = pd.DataFrame(data)
    
    # Styler le dataframe
    def color_risk(val):
        colors = {
            'Faible': 'background-color: #d4edda',
            'Modéré': 'background-color: #fff3cd',
            'Élevé': 'background-color: #f8d7da',
            'Critique': 'background-color: #f5c6cb'
        }
        return colors.get(val, '')
    
    styled_df = df.style.applymap(color_risk, subset=['Risque'])
    
    st.dataframe(styled_df, use_container_width=True)

def show_infractions_network():
    """Affiche le réseau des infractions connexes"""
    # Créer un graphe NetworkX
    G = nx.Graph()
    
    # Ajouter des nœuds (infractions)
    infractions = TYPES_INFRACTIONS[:8]
    for inf in infractions:
        G.add_node(inf)
    
    # Ajouter des liens aléatoires
    for i in range(15):
        inf1 = np.random.choice(infractions)
        inf2 = np.random.choice(infractions)
        if inf1 != inf2:
            weight = np.random.uniform(0.3, 1.0)
            G.add_edge(inf1, inf2, weight=weight)
    
    # Créer la visualisation PyVis
    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="#000000")
    net.from_nx(G)
    
    # Personnaliser l'apparence
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=150)
    
    # Sauvegarder et afficher
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, 'r') as f:
            html = f.read()
        st.components.v1.html(html, height=500)
        os.unlink(tmp.name)

def show_persons_network():
    """Affiche le réseau des personnes impliquées"""
    st.info("Réseau des personnes impliquées dans les affaires analysées")
    # Implémentation similaire à show_infractions_network

def show_jurisprudence_network():
    """Affiche le réseau des jurisprudences liées"""
    st.info("Réseau des jurisprudences citées et leurs relations")
    # Implémentation similaire

def show_complete_network():
    """Affiche le réseau complet"""
    st.info("Vue d'ensemble du réseau complet : infractions, personnes et jurisprudences")
    # Implémentation plus complexe combinant tous les éléments

def show_demo_data():
    """Affiche des données de démonstration"""
    st.markdown("### 🎯 Données de démonstration")
    st.info("Voici un aperçu des visualisations disponibles avec des données d'exemple")
    
    # Graphique d'exemple
    fig = px.scatter(
        x=np.random.randn(100),
        y=np.random.randn(100),
        color=np.random.choice(['Type A', 'Type B', 'Type C'], 100),
        title="Exemple de distribution des analyses"
    )
    st.plotly_chart(fig, use_container_width=True)

# Point d'entrée
if __name__ == "__main__":
    show()