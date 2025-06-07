# test_page.py (à créer à la racine du projet)
import streamlit as st
import sys
import os

st.title("Test de chargement des pages")

# Vérifier le chemin
st.write("Chemin actuel:", os.getcwd())
st.write("Python path:", sys.path)

# Essayer d'importer la page d'accueil
try:
    from pages import accueil
    st.success("✅ Module pages.accueil importé avec succès")
    
    # Vérifier si la fonction show existe
    if hasattr(accueil, 'show'):
        st.success("✅ Fonction show() trouvée")
        
        # Appeler la fonction
        st.header("Contenu de la page d'accueil:")
        accueil.show()
    else:
        st.error("❌ Fonction show() non trouvée dans pages.accueil")
        
except ImportError as e:
    st.error(f"❌ Erreur d'import: {e}")
except Exception as e:
    st.error(f"❌ Erreur: {e}")
    st.exception(e)