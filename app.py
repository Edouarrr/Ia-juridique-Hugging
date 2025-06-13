import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page
st.set_page_config(
    page_title="Mon Application Streamlit",
    page_icon="🚀",
    layout="wide"
)

# Titre principal
st.title("🚀 Mon Application Streamlit")
st.markdown("---")

# Barre latérale
st.sidebar.header("Navigation")
page = st.sidebar.selectbox(
    "Choisissez une page",
    ["Accueil", "Visualisations", "Données", "À propos"]
)

# Page d'accueil
if page == "Accueil":
    st.header("Bienvenue sur mon application !")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Fonctionnalités")
        st.write("""
        - Visualisation de données interactive
        - Téléchargement de fichiers CSV
        - Graphiques interactifs
        - Analyse statistique simple
        """)
    
    with col2:
        st.subheader("🎯 Objectifs")
        st.write("""
        Cette application a été créée pour :
        - Démontrer les capacités de Streamlit
        - Faciliter l'analyse de données
        - Créer des visualisations interactives
        """)
    
    # Widget interactif simple
    st.subheader("Testez un widget")
    name = st.text_input("Entrez votre nom :")
    if name:
        st.success(f"Bonjour {name} ! 👋")

# Page Visualisations
elif page == "Visualisations":
    st.header("📈 Visualisations de données")
    
    # Génération de données exemple
    st.subheader("Graphique exemple avec données aléatoires")
    
    # Paramètres
    col1, col2 = st.columns(2)
    with col1:
        nb_points = st.slider("Nombre de points", 10, 100, 50)
    with col2:
        type_graph = st.selectbox(
            "Type de graphique",
            ["Ligne", "Barres", "Nuage de points"]
        )
    
    # Création des données
    data = pd.DataFrame({
        'x': range(nb_points),
        'y': np.random.randn(nb_points).cumsum(),
        'z': np.random.randn(nb_points) * 10
    })
    
    # Affichage du graphique
    if type_graph == "Ligne":
        fig = px.line(data, x='x', y='y', title="Graphique en ligne")
    elif type_graph == "Barres":
        fig = px.bar(data, x='x', y='z', title="Graphique en barres")
    else:
        fig = px.scatter(data, x='x', y='y', size=abs(data['z']), 
                        title="Nuage de points", hover_data=['z'])
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Affichage des statistiques
    with st.expander("Voir les statistiques"):
        st.write(data.describe())

# Page Données
elif page == "Données":
    st.header("📁 Gestion des données")
    
    # Upload de fichier
    st.subheader("Télécharger un fichier CSV")
    uploaded_file = st.file_uploader(
        "Choisissez un fichier CSV",
        type=['csv']
    )
    
    if uploaded_file is not None:
        # Lecture du fichier
        df = pd.read_csv(uploaded_file)
        
        st.success("Fichier chargé avec succès !")
        
        # Aperçu des données
        st.subheader("Aperçu des données")
        st.write(f"Dimensions : {df.shape[0]} lignes × {df.shape[1]} colonnes")
        st.dataframe(df.head(10))
        
        # Colonnes disponibles
        st.subheader("Analyse rapide")
        col_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if col_numeric:
            col_choice = st.selectbox("Choisissez une colonne numérique", col_numeric)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Moyenne", f"{df[col_choice].mean():.2f}")
            with col2:
                st.metric("Médiane", f"{df[col_choice].median():.2f}")
            with col3:
                st.metric("Écart-type", f"{df[col_choice].std():.2f}")
            
            # Histogramme
            fig = px.histogram(df, x=col_choice, 
                             title=f"Distribution de {col_choice}")
            st.plotly_chart(fig, use_container_width=True)
    else:
        # Données exemple
        st.info("Aucun fichier téléchargé. Voici un exemple de données :")
        
        df_exemple = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=30, freq='D'),
            'Ventes': np.random.randint(100, 1000, 30),
            'Clients': np.random.randint(10, 100, 30),
            'Région': np.random.choice(['Nord', 'Sud', 'Est', 'Ouest'], 30)
        })
        
        st.dataframe(df_exemple)
        
        # Graphique exemple
        fig = px.line(df_exemple, x='Date', y='Ventes', 
                     title="Évolution des ventes sur 30 jours")
        st.plotly_chart(fig, use_container_width=True)

# Page À propos
else:
    st.header("ℹ️ À propos")
    
    st.markdown("""
    ### Application créée avec Streamlit
    
    Cette application démontre les capacités de Streamlit pour créer 
    rapidement des applications web interactives en Python.
    
    #### Technologies utilisées :
    - **Streamlit** : Framework principal
    - **Pandas** : Manipulation de données
    - **Plotly** : Visualisations interactives
    - **NumPy** : Calculs numériques
    
    #### Comment utiliser cette application :
    1. Naviguez entre les pages via le menu latéral
    2. Testez les widgets interactifs
    3. Téléchargez vos propres données CSV
    4. Explorez les visualisations
    
    ---
    
    **Version** : 1.0.0  
    **Date** : 2024  
    **Hébergement** : Hugging Face Spaces
    """)
    
    # Informations système
    with st.expander("Informations techniques"):
        st.code(f"""
Python : 3.x
Streamlit : {st.__version__}
Date actuelle : {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)

# Pied de page
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>Créé avec ❤️ en utilisant Streamlit</p>",
    unsafe_allow_html=True
)