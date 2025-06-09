# analyze_recherche.py
"""Script pour analyser recherche.py et identifier les fonctionnalités uniques"""

import re
import streamlit as st

def analyze_recherche_module():
    """Analyse le module recherche.py pour identifier les fonctionnalités"""
    
    st.title("🔍 Analyse du module recherche.py")
    
    # Charger le contenu de recherche.py
    try:
        with open('modules/recherche.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        st.error("Impossible de lire modules/recherche.py")
        return
    
    # 1. IDENTIFIER TOUTES LES FONCTIONS
    st.markdown("## 📋 Fonctions trouvées dans recherche.py")
    
    # Pattern pour trouver les définitions de fonctions
    function_pattern = r'^def\s+(\w+)\s*\([^)]*\):'
    functions = re.findall(function_pattern, content, re.MULTILINE)
    
    # Classer les fonctions par catégorie
    categories = {
        'plainte': [],
        'redaction': [],
        'analysis': [],
        'bordereau': [],
        'jurisprudence': [],
        'timeline': [],
        'mapping': [],
        'import_export': [],
        'email': [],
        'search': [],
        'ui': [],
        'utils': [],
        'autres': []
    }
    
    # Catégoriser chaque fonction
    for func in functions:
        func_lower = func.lower()
        
        if 'plainte' in func_lower:
            categories['plainte'].append(func)
        elif any(word in func_lower for word in ['redaction', 'generate_document', 'rediger']):
            categories['redaction'].append(func)
        elif any(word in func_lower for word in ['analysis', 'analyze', 'analyse']):
            categories['analysis'].append(func)
        elif 'bordereau' in func_lower:
            categories['bordereau'].append(func)
        elif 'jurisprudence' in func_lower or 'juris' in func_lower:
            categories['jurisprudence'].append(func)
        elif 'timeline' in func_lower or 'chronolog' in func_lower:
            categories['timeline'].append(func)
        elif 'mapping' in func_lower or 'cartograph' in func_lower:
            categories['mapping'].append(func)
        elif any(word in func_lower for word in ['import', 'export']):
            categories['import_export'].append(func)
        elif 'email' in func_lower or 'mail' in func_lower:
            categories['email'].append(func)
        elif 'search' in func_lower or 'recherche' in func_lower:
            categories['search'].append(func)
        elif any(word in func_lower for word in ['show', 'display', 'render']):
            categories['ui'].append(func)
        elif any(word in func_lower for word in ['collect', 'extract', 'calculate', 'format']):
            categories['utils'].append(func)
        else:
            categories['autres'].append(func)
    
    # Afficher par catégorie
    for cat, funcs in categories.items():
        if funcs:
            with st.expander(f"{cat.upper()} ({len(funcs)} fonctions)", expanded=True):
                for func in funcs:
                    st.write(f"- `{func}()`")
    
    # 2. IDENTIFIER LES FONCTIONNALITÉS SPÉCIALES
    st.markdown("## 🌟 Fonctionnalités potentiellement uniques")
    
    # Chercher les fonctions de génération de plainte avancées
    plainte_features = []
    
    # Pattern pour la génération de plainte avec CPC
    if 'partie civile' in content or 'constitution de partie civile' in content:
        plainte_features.append("✅ Génération de plainte avec constitution de partie civile")
    
    # Pattern pour l'enrichissement avec CompanyInfoManager
    if 'CompanyInfoManager' in content:
        plainte_features.append("✅ Enrichissement des informations des parties (sociétés)")
    
    # Pattern pour la vérification des jurisprudences
    if 'verify_jurisprudences_in_analysis' in content:
        plainte_features.append("✅ Vérification automatique des jurisprudences citées")
    
    # Pattern pour les suggestions d'amélioration
    if 'suggestions d\'amélioration' in content.lower():
        plainte_features.append("✅ Suggestions d'amélioration des documents")
    
    # Pattern pour la comparaison multi-IA
    if 'compare_all_providers' in content:
        plainte_features.append("✅ Comparaison des résultats entre plusieurs IA")
    
    if plainte_features:
        st.markdown("### 📝 Fonctionnalités de plainte avancées")
        for feature in plainte_features:
            st.write(feature)
    
    # 3. ANALYSER LES PROMPTS COMPLEXES
    st.markdown("## 💬 Prompts spécialisés trouvés")
    
    # Chercher les prompts longs (plus de 500 caractères)
    prompt_pattern = r'prompt\s*=\s*f?"""([^"]{500,})"""'
    long_prompts = re.findall(prompt_pattern, content, re.DOTALL)
    
    if long_prompts:
        st.write(f"Trouvé {len(long_prompts)} prompts complexes")
        
        for i, prompt in enumerate(long_prompts[:3], 1):  # Limiter à 3
            with st.expander(f"Prompt {i} ({len(prompt)} caractères)"):
                st.text(prompt[:500] + "...")
    
    # 4. IDENTIFIER LES INTÉGRATIONS SPÉCIALES
    st.markdown("## 🔌 Intégrations spéciales")
    
    integrations = []
    
    # Vérifier les managers utilisés
    managers = [
        'CompanyInfoManager',
        'StyleAnalyzer', 
        'DynamicGenerators',
        'DocumentManager',
        'JurisprudenceVerifier',
        'LegalSearchManager'
    ]
    
    for manager in managers:
        if manager in content:
            integrations.append(f"✅ {manager}")
    
    if integrations:
        for integration in integrations:
            st.write(integration)
    
    # 5. STATISTIQUES GÉNÉRALES
    st.markdown("## 📊 Statistiques")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Lignes de code", content.count('\n'))
    
    with col2:
        st.metric("Fonctions", len(functions))
    
    with col3:
        st.metric("Imports", content.count('import '))
    
    # 6. RECOMMANDATIONS
    st.markdown("## 💡 Recommandations")
    
    st.info("""
    **Pour préserver les fonctionnalités uniques :**
    
    1. **Créez un module `advanced_features.py`** pour les fonctionnalités qui n'existent dans aucun autre module
    
    2. **Enrichissez les modules existants** avec les fonctionnalités manquantes :
       - `plainte_advanced.py` pour la génération avancée de plaintes
       - `analysis_advanced.py` pour la vérification des jurisprudences
    
    3. **Documentez les dépendances** entre les modules
    """)
    
    # Générer un rapport
    if st.button("📄 Générer rapport complet"):
        report = generate_analysis_report(categories, plainte_features, integrations)
        st.download_button(
            "💾 Télécharger le rapport",
            report,
            "analyse_recherche_py.txt",
            "text/plain"
        )

def generate_analysis_report(categories, features, integrations):
    """Génère un rapport détaillé de l'analyse"""
    
    report = "ANALYSE DU MODULE RECHERCHE.PY\n"
    report += "=" * 50 + "\n\n"
    
    report += "FONCTIONS PAR CATÉGORIE\n"
    report += "-" * 30 + "\n"
    
    for cat, funcs in categories.items():
        if funcs:
            report += f"\n{cat.upper()} ({len(funcs)} fonctions):\n"
            for func in funcs:
                report += f"  - {func}()\n"
    
    report += "\n\nFONCTIONNALITÉS UNIQUES IDENTIFIÉES\n"
    report += "-" * 30 + "\n"
    
    for feature in features:
        report += f"{feature}\n"
    
    report += "\n\nINTÉGRATIONS SPÉCIALES\n"
    report += "-" * 30 + "\n"
    
    for integration in integrations:
        report += f"{integration}\n"
    
    return report

# Lancer l'analyse si exécuté directement
if __name__ == "__main__":
    analyze_recherche_module()