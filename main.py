# Test sécurisé
if st.sidebar.checkbox("🧪 Nouvelle version"):
    from modules import recherche_simplified
    recherche_simplified.show_page()
else:
    # Votre code actuel
    from modules import recherche
    recherche.show_page()