"""Script de test pour vérifier l'intégration du module juridique"""

import streamlit as st
import sys
import os

# Ajouter le répertoire parent au path si nécessaire
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Teste que tous les imports fonctionnent"""
    st.header("🧪 Test des imports")
    
    imports_status = {}
    
    # Test du cahier des charges
    try:
        from config.cahier_des_charges import (
            CABINET_INFO, 
            STRUCTURES_ACTES,
            validate_acte
        )
        imports_status['config.cahier_des_charges'] = "✅ OK"
    except ImportError as e:
        imports_status['config.cahier_des_charges'] = f"❌ Erreur: {str(e)}"
    
    # Test du module de génération
    try:
        from modules.generation_juridique import (
            GenerateurActesJuridiques,
            ActeJuridique
        )
        imports_status['modules.generation_juridique'] = "✅ OK"
    except ImportError as e:
        imports_status['modules.generation_juridique'] = f"❌ Erreur: {str(e)}"
    
    # Test du module d'intégration
    try:
        from modules.integration_juridique import (
            AnalyseurRequeteJuridique,
            enhance_search_with_generation
        )
        imports_status['modules.integration_juridique'] = "✅ OK"
    except ImportError as e:
        imports_status['modules.integration_juridique'] = f"❌ Erreur: {str(e)}"
    
    # Afficher les résultats
    for module, status in imports_status.items():
        st.write(f"**{module}:** {status}")
    
    return all("✅" in status for status in imports_status.values())

def test_analyseur():
    """Teste l'analyseur de requêtes juridiques"""
    st.header("🔍 Test de l'analyseur juridique")
    
    try:
        from modules.integration_juridique import AnalyseurRequeteJuridique
        
        analyseur = AnalyseurRequeteJuridique()
        
        # Cas de test
        test_cases = [
            "rédiger plainte contre Vinci pour abus de biens sociaux",
            "créer conclusions de nullité @affaire_martin",
            "générer plainte avec constitution de partie civile contre A, B et C",
            "écrire observations article 175 CPP",
            "simple recherche sans génération"
        ]
        
        for query in test_cases:
            st.write(f"\n**Requête:** `{query}`")
            
            analyse = analyseur.analyser_requete(query)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Génération détectée:**", "✅" if analyse['is_generation'] else "❌")
                st.write("**Type d'acte:**", analyse['type_acte'] or "Non détecté")
            
            with col2:
                st.write("**Parties:**")
                if analyse['parties']['defendeurs']:
                    st.write("- Défendeurs:", ', '.join(analyse['parties']['defendeurs']))
                else:
                    st.write("- Aucune partie détectée")
            
            with col3:
                st.write("**Infractions:**")
                if analyse['infractions']:
                    st.write("- ", ', '.join(analyse['infractions']))
                else:
                    st.write("- Aucune infraction détectée")
            
            st.markdown("---")
        
        return True
        
    except Exception as e:
        st.error(f"Erreur lors du test de l'analyseur: {str(e)}")
        return False

def test_generation_simple():
    """Teste la génération d'un acte simple"""
    st.header("📝 Test de génération d'acte")
    
    try:
        from modules.generation_juridique import GenerateurActesJuridiques
        
        generateur = GenerateurActesJuridiques()
        
        # Paramètres de test
        params_test = {
            'parties': {
                'demandeurs': ['M. Test'],
                'defendeurs': ['Société Example SAS']
            },
            'infractions': ['Abus de biens sociaux'],
            'contexte': 'Test de génération',
            'pieces': [
                {'titre': 'Pièce test 1', 'date': '01/01/2024'},
                {'titre': 'Pièce test 2', 'date': '02/01/2024'}
            ]
        }
        
        with st.spinner("Génération en cours..."):
            # Générer une plainte simple
            acte = generateur.generer_acte('plainte_simple', params_test)
            
            st.success("✅ Acte généré avec succès !")
            
            # Afficher les métadonnées
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Type", acte.type_acte)
            with col2:
                st.metric("Mots", f"{acte.metadata['longueur_mots']:,}")
            with col3:
                st.metric("Pièces", len(acte.pieces))
            
            # Afficher un extrait
            st.text_area(
                "Extrait de l'acte généré",
                value=acte.contenu[:500] + "...",
                height=200
            )
            
            return True
            
    except Exception as e:
        st.error(f"Erreur lors de la génération: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return False

def test_validation():
    """Teste la validation selon le cahier des charges"""
    st.header("✅ Test de validation CDC")
    
    try:
        from config.cahier_des_charges import validate_acte
        
        # Créer un contenu test
        contenu_test = "Test " * 500  # 500 mots
        
        # Tester la validation
        validation = validate_acte(contenu_test, 'plainte_simple')
        
        if validation['valid']:
            st.success("✅ Document valide selon le CDC")
        else:
            st.warning("⚠️ Document non conforme")
            
        st.write("**Nombre de mots:**", validation['word_count'])
        
        if validation['errors']:
            st.write("**Erreurs:**")
            for error in validation['errors']:
                st.error(f"- {error}")
                
        if validation['warnings']:
            st.write("**Avertissements:**")
            for warning in validation['warnings']:
                st.warning(f"- {warning}")
        
        return True
        
    except Exception as e:
        st.error(f"Erreur lors de la validation: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    st.set_page_config(
        page_title="Test Intégration Juridique",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 Test d'intégration du module juridique")
    
    st.info("""
    Ce script teste l'intégration du cahier des charges juridique dans votre application.
    Il vérifie que tous les modules sont correctement installés et fonctionnent.
    """)
    
    # Tests
    all_tests_passed = True
    
    # Test 1 : Imports
    if test_imports():
        st.success("✅ Tous les imports fonctionnent")
    else:
        st.error("❌ Certains imports ont échoué")
        all_tests_passed = False
        st.stop()
    
    st.markdown("---")
    
    # Test 2 : Analyseur
    if test_analyseur():
        st.success("✅ L'analyseur juridique fonctionne")
    else:
        st.error("❌ L'analyseur juridique a échoué")
        all_tests_passed = False
    
    st.markdown("---")
    
    # Test 3 : Génération
    if test_generation_simple():
        st.success("✅ La génération d'actes fonctionne")
    else:
        st.error("❌ La génération a échoué")
        all_tests_passed = False
    
    st.markdown("---")
    
    # Test 4 : Validation
    if test_validation():
        st.success("✅ La validation CDC fonctionne")
    else:
        st.error("❌ La validation a échoué")
        all_tests_passed = False
    
    # Résultat final
    st.markdown("---")
    st.header("📊 Résultat des tests")
    
    if all_tests_passed:
        st.balloons()
        st.success("""
        🎉 **Tous les tests sont passés !**
        
        Votre intégration est fonctionnelle. Vous pouvez maintenant :
        - Utiliser la commande `rédiger plainte contre X pour Y` dans la recherche
        - Cliquer sur le bouton "⚖️ Actes juridiques" 
        - Générer tous types d'actes juridiques conformes au cahier des charges
        """)
    else:
        st.error("""
        ❌ **Certains tests ont échoué**
        
        Vérifiez :
        1. Que tous les fichiers sont créés aux bons endroits
        2. Que les imports sont corrects
        3. Les messages d'erreur ci-dessus pour plus de détails
        """)
    
    # Test interactif
    st.markdown("---")
    st.header("🎮 Test interactif")
    
    query = st.text_input(
        "Testez une requête juridique",
        value="rédiger plainte contre Société ABC pour corruption",
        help="Exemples : rédiger plainte, créer conclusions, générer assignation..."
    )
    
    if st.button("Analyser la requête"):
        try:
            from modules.integration_juridique import AnalyseurRequeteJuridique
            
            analyseur = AnalyseurRequeteJuridique()
            analyse = analyseur.analyser_requete(query)
            
            st.json(analyse)
            
        except Exception as e:
            st.error(f"Erreur: {str(e)}")

if __name__ == "__main__":
    main()