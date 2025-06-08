# modules/recherche.py
"""Page de recherche unifiée avec analyse IA intégrée"""

import streamlit as st
import asyncio
from datetime import datetime
import re

from config.app_config import SearchMode, ANALYSIS_PROMPTS_AFFAIRES, LLMProvider
from managers.azure_blob_manager import AzureBlobManager
from managers.azure_search_manager import AzureSearchManager
from managers.multi_llm_manager import MultiLLMManager
from managers.document_manager import display_import_interface
from managers.dynamic_generators import generate_dynamic_search_prompts
from managers.legal_search import LegalSearchManager, display_legal_search_interface
from models.dataclasses import Document
from utils.helpers import clean_key

def show_page():
    """Affiche la page de recherche unifiée"""
    st.header("🔍 Recherche & Analyse Intelligente")
    
    # BARRE DE RECHERCHE UNIFIÉE
    show_unified_search_interface()
    
    # Onglets pour les fonctionnalités avancées
    tabs = st.tabs([
        "📊 Résultats & Analyse", 
        "⚖️ Jurisprudence", 
        "🗂️ Explorateur", 
        "📤 Import",
        "🤖 IA Avancée"
    ])
    
    with tabs[0]:
        show_results_and_analysis_tab()
    
    with tabs[1]:
        show_jurisprudence_tab()
    
    with tabs[2]:
        show_azure_explorer_tab()
    
    with tabs[3]:
        show_import_tab()
    
    with tabs[4]:
        show_advanced_ai_tab()

def show_unified_search_interface():
    """Interface de recherche unifiée"""
    
    st.markdown("""
    ### 🎯 Recherche Intelligente
    
    **Modes d'utilisation :**
    - `contrats` → Recherche normale
    - `@affaire_martin` → Référence spécifique
    - `@contrats analyser les clauses` → Référence + Question IA
    """)
    
    # BARRE DE RECHERCHE PRINCIPALE
    search_query = st.text_input(
        "🔍 Recherche ou Question IA",
        value=st.session_state.get('search_query', ''),
        placeholder="Ex: @affaire_martin quels sont les moyens de défense disponibles ?",
        key="unified_search_input",
        help="Tapez votre recherche ou @référence + question pour l'IA"
    )
    
    # ANALYSE DE LA REQUÊTE EN TEMPS RÉEL
    if search_query:
        query_analysis = analyze_search_query(search_query)
        display_query_analysis(query_analysis)
    
    # DÉCLENCHEMENT AUTO
    if search_query and search_query != st.session_state.get('last_unified_query', ''):
        st.session_state.last_unified_query = search_query
        process_unified_query(search_query)
    
    # OPTIONS RAPIDES
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_type = st.selectbox(
            "Type",
            ["🔍 Auto", "📁 Dossiers", "📄 Fichiers", "🔗 Référence"],
            key="search_type_unified"
        )
    
    with col2:
        if st.button("🗑️ Effacer", key="clear_unified"):
            clear_search_state()
    
    with col3:
        if st.button("🔄 Relancer", key="rerun_unified"):
            if search_query:
                process_unified_query(search_query)
    
    with col4:
        ai_mode = st.checkbox("🤖 Forcer IA", key="force_ai_mode", help="Force l'analyse IA même sans @")

def analyze_search_query(query: str) -> dict:
    """Analyse la requête pour déterminer le type et les actions"""
    analysis = {
        'type': 'simple',
        'has_reference': False,
        'has_ai_question': False,
        'reference': None,
        'ai_question': None,
        'search_terms': [],
        'confidence': 0.0
    }
    
    # Vérifier si c'est une référence
    if query.startswith('@'):
        analysis['has_reference'] = True
        analysis['type'] = 'reference'
        
        # Séparer référence et question IA
        parts = query[1:].split(' ', 1)  # Enlever @ et séparer
        analysis['reference'] = parts[0].strip()
        
        if len(parts) > 1 and parts[1].strip():
            analysis['has_ai_question'] = True
            analysis['ai_question'] = parts[1].strip()
            analysis['type'] = 'reference_with_ai'
            analysis['confidence'] = 0.9
        else:
            analysis['confidence'] = 0.7
    
    else:
        # Recherche normale
        analysis['search_terms'] = query.split()
        analysis['confidence'] = 0.6
        
        # Détecter si c'est probablement une question IA
        ai_indicators = [
            'analyser', 'analyse', 'quels sont', 'comment', 'pourquoi',
            'moyens de défense', 'stratégie', 'risques', 'recommandations',
            'jurisprudence', 'précédents', 'sanctions', 'prescription'
        ]
        
        if any(indicator in query.lower() for indicator in ai_indicators):
            analysis['has_ai_question'] = True
            analysis['ai_question'] = query
            analysis['type'] = 'ai_question'
            analysis['confidence'] = 0.8
    
    return analysis

def display_query_analysis(analysis: dict):
    """Affiche l'analyse de la requête"""
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if analysis['type'] == 'reference_with_ai':
            st.success(f"🎯 Référence + IA: @{analysis['reference']}")
        elif analysis['type'] == 'reference':
            st.info(f"🔗 Référence: @{analysis['reference']}")
        elif analysis['type'] == 'ai_question':
            st.warning("🤖 Question IA détectée")
        else:
            st.caption("🔍 Recherche standard")
    
    with col2:
        if analysis['has_ai_question']:
            st.caption(f"💭 Question: {analysis['ai_question'][:40]}...")
    
    with col3:
        confidence_color = "🟢" if analysis['confidence'] > 0.8 else "🟡" if analysis['confidence'] > 0.6 else "🔴"
        st.caption(f"{confidence_color} {analysis['confidence']:.0%}")

def process_unified_query(query: str):
    """Traite la requête unifiée"""
    analysis = analyze_search_query(query)
    
    # Réinitialiser les résultats
    st.session_state.search_results = []
    st.session_state.ai_analysis_results = {}
    st.session_state.query_analysis = analysis
    
    with st.spinner("🔄 Traitement de votre requête..."):
        
        # 1. RECHERCHE DE DOCUMENTS
        if analysis['has_reference']:
            # Recherche par référence
            search_results = search_by_reference(f"@{analysis['reference']}")
        else:
            # Recherche normale
            search_type = st.session_state.get('search_type_unified', '🔍 Auto')
            if '📁' in search_type:
                search_results = search_folders(query)
            elif '📄' in search_type:
                search_results = search_files(query)
            else:
                # Auto : essayer tous les types
                search_results = search_auto(query)
        
        st.session_state.search_results = search_results
        
        # 2. ANALYSE IA SI DEMANDÉE
        if analysis['has_ai_question'] or st.session_state.get('force_ai_mode', False):
            if search_results:
                ai_question = analysis['ai_question'] or query
                ai_results = perform_ai_analysis(search_results, ai_question, analysis['reference'])
                st.session_state.ai_analysis_results = ai_results
            else:
                st.warning("⚠️ Aucun document trouvé pour l'analyse IA")

def search_auto(query: str):
    """Recherche automatique (tous types)"""
    results = []
    
    # Recherche fichiers
    file_results = search_files(query)
    results.extend(file_results)
    
    # Recherche dossiers
    folder_results = search_folders(query)
    results.extend(folder_results)
    
    # Recherche par référence si ça ressemble à une référence
    if len(query.split()) == 1:  # Un seul mot
        ref_results = search_by_reference(f"@{query}")
        results.extend(ref_results)
    
    # Trier par pertinence
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return results

def perform_ai_analysis(search_results: list, question: str, reference: str = None) -> dict:
    """Effectue l'analyse IA sur les documents trouvés"""
    
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        return {'error': 'Aucune IA disponible'}
    
    # Préparer le contexte des documents
    context = prepare_documents_context(search_results)
    
    if not context:
        return {'error': 'Aucun contenu analysable'}
    
    # Construire le prompt d'analyse
    analysis_prompt = build_ai_analysis_prompt(question, context, reference)
    
    # Sélectionner les IA à utiliser
    available_providers = list(llm_manager.clients.keys())
    selected_providers = available_providers[:2]  # Utiliser 2 IA max pour la rapidité
    
    # Exécuter l'analyse
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        responses = loop.run_until_complete(
            llm_manager.query_multiple_llms(
                selected_providers,
                analysis_prompt,
                "Tu es un avocat expert en droit pénal des affaires français."
            )
        )
        
        # Fusionner les réponses
        if len(responses) > 1:
            fusion = llm_manager.fusion_responses(responses)
        else:
            fusion = responses[0]['response'] if responses and responses[0]['success'] else "Analyse non disponible"
        
        return {
            'success': True,
            'analysis': fusion,
            'providers_used': [r['provider'] for r in responses if r['success']],
            'document_count': len(search_results),
            'question': question,
            'reference': reference
        }
        
    except Exception as e:
        return {'error': f'Erreur analyse IA: {str(e)}'}

def prepare_documents_context(search_results: list) -> str:
    """Prépare le contexte des documents pour l'IA"""
    context_parts = []
    
    blob_manager = st.session_state.get('azure_blob_manager')
    
    for i, result in enumerate(search_results[:10]):  # Limiter à 10 documents
        
        doc_content = ""
        
        # Récupérer le contenu selon le type
        if result.get('type') == 'file' and 'container' in result:
            # Fichier Azure
            try:
                if blob_manager and blob_manager.is_connected():
                    content_bytes = blob_manager.download_blob(result['container'], result['path'])
                    doc_content = content_bytes.decode('utf-8', errors='ignore')[:2000]  # Limiter
            except:
                doc_content = result.get('content', '')
        
        elif result.get('type') == 'folder':
            # Dossier : récupérer les premiers fichiers
            doc_content = f"Dossier {result['title']} - {result.get('content', '')}"
            
        else:
            # Document local ou autre
            doc_content = result.get('content', '')
        
        if doc_content:
            context_parts.append(f"""
=== DOCUMENT {i+1}: {result['title']} ===
Source: {result.get('source', 'Unknown')}
Contenu: {doc_content[:1500]}...
""")
    
    return "\n".join(context_parts)

def build_ai_analysis_prompt(question: str, context: str, reference: str = None) -> str:
    """Construit le prompt d'analyse pour l'IA"""
    
    prompt = f"""ANALYSE JURIDIQUE DEMANDÉE

Question posée : {question}
"""
    
    if reference:
        prompt += f"Référence spécifique : @{reference}\n"
    
    prompt += f"""
Documents à analyser :
{context}

INSTRUCTIONS :
1. Analyse approfondie des documents fournis
2. Réponse structurée et précise à la question posée
3. Références aux documents analysés
4. Moyens juridiques et recommandations pratiques
5. Mise en évidence des points clés

Réponds de manière structurée avec :
- 🎯 RÉPONSE DIRECTE
- 📋 ANALYSE DÉTAILLÉE  
- ⚖️ MOYENS JURIDIQUES
- 🛡️ RECOMMANDATIONS
- 📚 RÉFÉRENCES UTILES
"""
    
    return prompt

def clear_search_state():
    """Remet à zéro l'état de recherche"""
    keys_to_clear = [
        'search_query', 'last_unified_query', 'search_results', 
        'ai_analysis_results', 'query_analysis', 'selected_folders'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            if key == 'selected_folders':
                st.session_state[key].clear()
            else:
                del st.session_state[key]
    
    st.rerun()

def show_results_and_analysis_tab():
    """Onglet unifié résultats + analyse"""
    
    # Afficher l'analyse de la requête
    if 'query_analysis' in st.session_state:
        analysis = st.session_state.query_analysis
        
        with st.expander("🔍 Analyse de votre requête", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type :** {analysis['type']}")
                if analysis['reference']:
                    st.write(f"**Référence :** @{analysis['reference']}")
            
            with col2:
                st.write(f"**Confiance :** {analysis['confidence']:.0%}")
                if analysis['ai_question']:
                    st.write(f"**Question IA :** {analysis['ai_question'][:50]}...")
    
    # RÉSULTATS IA EN PREMIER (si disponibles)
    if 'ai_analysis_results' in st.session_state and st.session_state.ai_analysis_results:
        show_ai_analysis_results()
    
    # RÉSULTATS DE RECHERCHE
    if 'search_results' in st.session_state and st.session_state.search_results:
        show_search_results_unified()
    
    # Si rien n'est trouvé
    if not st.session_state.get('search_results') and not st.session_state.get('ai_analysis_results'):
        if st.session_state.get('last_unified_query'):
            st.info("🔍 Aucun résultat trouvé. Essayez une autre recherche.")

def show_ai_analysis_results():
    """Affiche les résultats d'analyse IA"""
    results = st.session_state.ai_analysis_results
    
    if 'error' in results:
        st.error(f"❌ {results['error']}")
        return
    
    st.markdown("### 🤖 Analyse IA")
    
    # Métadonnées de l'analyse
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents analysés", results.get('document_count', 0))
    
    with col2:
        providers = results.get('providers_used', [])
        st.metric("IA utilisées", len(providers))
    
    with col3:
        if st.button("💾 Exporter analyse", key="export_ai_analysis"):
            export_ai_analysis(results)
    
    # Résultat de l'analyse
    with st.container():
        st.markdown("#### 📊 Résultat de l'analyse")
        
        if 'analysis' in results:
            st.markdown(results['analysis'])
        
        # Informations sur les providers utilisés
        if providers:
            with st.expander("🔧 Détails techniques", expanded=False):
                st.write(f"**Question analysée :** {results.get('question', 'N/A')}")
                st.write(f"**Référence :** @{results.get('reference', 'N/A')}")
                st.write(f"**IA utilisées :** {', '.join(providers)}")
    
    # Actions rapides
    st.markdown("#### ⚡ Actions rapides")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Générer acte", key="generate_act_from_analysis"):
            generate_act_from_analysis(results)
    
    with col2:
        if st.button("📋 Créer synthèse", key="create_synthesis"):
            create_synthesis_from_analysis(results)
    
    with col3:
        if st.button("🔄 Analyser plus", key="deeper_analysis"):
            perform_deeper_analysis(results)

def show_search_results_unified():
    """Affiche les résultats de recherche de manière unifiée"""
    results = st.session_state.search_results
    
    st.markdown(f"### 📁 Documents trouvés ({len(results)})")
    
    # Grouper par type
    folders = [r for r in results if r.get('type') == 'folder']
    files = [r for r in results if r.get('type') == 'file']
    others = [r for r in results if r.get('type') not in ['folder', 'file']]
    
    # Affichage par onglets
    if folders or files or others:
        result_tabs = []
        if folders:
            result_tabs.append(f"📁 Dossiers ({len(folders)})")
        if files:
            result_tabs.append(f"📄 Fichiers ({len(files)})")
        if others:
            result_tabs.append(f"📋 Autres ({len(others)})")
        
        if len(result_tabs) > 1:
            selected_tab = st.tabs(result_tabs)
            
            tab_index = 0
            if folders:
                with selected_tab[tab_index]:
                    show_folder_results_unified(folders)
                tab_index += 1
            
            if files:
                with selected_tab[tab_index]:
                    show_file_results_unified(files)
                tab_index += 1
            
            if others:
                with selected_tab[tab_index]:
                    show_other_results_unified(others)
        else:
            # Un seul type, afficher directement
            if folders:
                show_folder_results_unified(folders)
            elif files:
                show_file_results_unified(files)
            else:
                show_other_results_unified(others)

def show_folder_results_unified(folders):
    """Affiche les dossiers trouvés avec actions rapides"""
    
    # Sélection multiple
    if 'selected_folders' not in st.session_state:
        st.session_state.selected_folders = set()
    
    # Actions groupées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Tout sélectionner", key="select_all_unified"):
            st.session_state.selected_folders = {f['id'] for f in folders}
            st.rerun()
    
    with col2:
        if st.button("❌ Tout désélectionner", key="deselect_all_unified"):
            st.session_state.selected_folders.clear()
            st.rerun()
    
    with col3:
        if st.button("📥 Ajouter sélection", key="add_selected_unified"):
            add_selected_folders_to_analysis()
    
    with col4:
        selected_count = len(st.session_state.selected_folders)
        if selected_count > 0:
            st.success(f"✅ {selected_count}")
    
    # Liste des dossiers
    for folder in folders:
        with st.container():
            col1, col2, col3 = st.columns([0.5, 4, 1])
            
            with col1:
                is_selected = folder['id'] in st.session_state.selected_folders
                if st.checkbox("", value=is_selected, key=f"check_unified_{folder['id']}"):
                    st.session_state.selected_folders.add(folder['id'])
                else:
                    st.session_state.selected_folders.discard(folder['id'])
            
            with col2:
                st.markdown(f"**{folder['title']}**")
                st.caption(f"📂 {folder['content']} | {folder['source']}")
            
            with col3:
                if st.button("🤖 Analyser", key=f"analyze_folder_{folder['id']}"):
                    analyze_single_folder(folder)

def show_file_results_unified(files):
    """Affiche les fichiers trouvés"""
    for file in files:
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**{file['title']}**")
                st.caption(f"📄 {file.get('content', '')} | {file['source']}")
            
            with col2:
                if st.button("🤖", key=f"analyze_file_{file['id']}", help="Analyser ce fichier"):
                    analyze_single_file(file)

def show_other_results_unified(others):
    """Affiche les autres résultats"""
    for item in others:
        with st.container():
            st.markdown(f"**{item['title']}**")
            st.caption(f"📋 {item.get('content', '')} | {item['source']}")

def add_selected_folders_to_analysis():
    """Ajoute les dossiers sélectionnés à l'analyse"""
    if not st.session_state.selected_folders:
        st.warning("⚠️ Aucun dossier sélectionné")
        return
    
    # Récupérer les dossiers sélectionnés
    selected_folders = []
    for folder_id in st.session_state.selected_folders:
        for result in st.session_state.search_results:
            if result['id'] == folder_id:
                selected_folders.append(result)
    
    # Lancer l'analyse IA sur ces dossiers
    if selected_folders:
        question = st.text_input(
            "Question pour l'analyse",
            "Analyser le contenu de ces dossiers",
            key="question_selected_folders"
        )
        
        if st.button("🚀 Analyser les dossiers sélectionnés", key="analyze_selected_now"):
            ai_results = perform_ai_analysis(selected_folders, question)
            st.session_state.ai_analysis_results = ai_results
            st.rerun()

def analyze_single_folder(folder):
    """Analyse un dossier unique"""
    question = f"Analyser le contenu du dossier {folder['title']}"
    ai_results = perform_ai_analysis([folder], question, folder.get('name'))
    st.session_state.ai_analysis_results = ai_results
    st.rerun()

def analyze_single_file(file):
    """Analyse un fichier unique"""
    question = f"Analyser le fichier {file['title']}"
    ai_results = perform_ai_analysis([file], question)
    st.session_state.ai_analysis_results = ai_results
    st.rerun()

def export_ai_analysis(results):
    """Exporte l'analyse IA"""
    content = f"""ANALYSE IA - {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
Question: {results.get('question', 'N/A')}
Référence: @{results.get('reference', 'N/A')}
Documents analysés: {results.get('document_count', 0)}
IA utilisées: {', '.join(results.get('providers_used', []))}

RÉSULTAT:
{results.get('analysis', 'Aucune analyse disponible')}
"""
    
    st.download_button(
        "💾 Télécharger l'analyse",
        content,
        f"analyse_ia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        "text/plain",
        key="download_ai_analysis"
    )

def generate_act_from_analysis(results):
    """Génère un acte à partir de l'analyse"""
    st.info("📝 Fonction de génération d'acte à implémenter")

def create_synthesis_from_analysis(results):
    """Crée une synthèse à partir de l'analyse"""
    st.info("📋 Fonction de synthèse à implémenter")

def perform_deeper_analysis(results):
    """Effectue une analyse plus approfondie"""
    st.info("🔬 Fonction d'analyse approfondie à implémenter")

# Fonctions de recherche réutilisées (search_by_reference, search_folders, search_files, etc.)
# [Reprendre les fonctions de recherche de la version précédente]

def search_by_reference(query: str):
    """Recherche par référence @ (fonction simplifiée)"""
    if not query.startswith('@'):
        return []
    
    reference = query[1:].lower().strip()
    results = []
    
    # Recherche dans Azure Blob
    blob_manager = st.session_state.get('azure_blob_manager')
    if blob_manager and blob_manager.is_connected():
        containers = blob_manager.list_containers()
        
        for container in containers:
            try:
                items = blob_manager.list_folder_contents(container, "")
                
                for item in items:
                    if reference in item['name'].lower():
                        results.append({
                            'id': f"ref_{container}_{item['name']}",
                            'title': f"{'📁' if item['type'] == 'folder' else '📄'} {item['name']}",
                            'content': f"Trouvé par référence @{reference}",
                            'score': 1.0,
                            'source': f"Azure: {container}",
                            'type': item['type'],
                            'path': item['path'],
                            'container': container
                        })
            except:
                continue
    
    return results

def search_folders(query: str):
    """Recherche de dossiers (fonction simplifiée)"""
    results = []
    blob_manager = st.session_state.get('azure_blob_manager')
    
    if blob_manager and blob_manager.is_connected():
        containers = blob_manager.list_containers()
        
        for container in containers:
            try:
                items = blob_manager.list_folder_contents(container, "")
                
                for item in items:
                    if item['type'] == 'folder' and query.lower() in item['name'].lower():
                        results.append({
                            'id': f"folder_{container}_{item['name']}",
                            'title': f"📁 {item['name']}",
                            'content': f"Dossier dans {container}",
                            'score': 1.0,
                            'source': f"Azure: {container}",
                            'type': 'folder',
                            'path': item['path'],
                            'container': container
                        })
            except:
                continue
    
    return results

def search_files(query: str):
    """Recherche de fichiers (fonction simplifiée)"""
    results = []
    
    # Recherche locale d'abord
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if query.lower() in doc.title.lower() or query.lower() in doc.content.lower():
            results.append({
                'id': doc_id,
                'title': doc.title,
                'content': doc.content[:200] + "...",
                'score': 1.0,
                'source': doc.source,
                'type': 'document'
            })
    
    return results

# Fonctions pour les autres onglets
def show_jurisprudence_tab():
    """Onglet de recherche juridique"""
    display_legal_search_interface()

def show_azure_explorer_tab():
    """Onglet d'exploration Azure"""
    st.info("🗂️ Utilisez l'onglet principal pour une exploration complète")

def show_import_tab():
    """Onglet d'import"""
    display_import_interface()

def show_advanced_ai_tab():
    """Onglet IA avancée"""
    st.markdown("### 🤖 IA Avancée")
    
    # Sélection manuelle des IA
    llm_manager = MultiLLMManager()
    available_providers = list(llm_manager.clients.keys())
    
    if available_providers:
        selected_providers = st.multiselect(
            "Sélectionner les IA",
            [p.value for p in available_providers],
            default=[available_providers[0].value],
            key="advanced_ai_providers"
        )
        
        # Question personnalisée
        custom_question = st.text_area(
            "Question personnalisée",
            placeholder="Posez votre question juridique...",
            key="custom_ai_question"
        )
        
        if st.button("🚀 Lancer analyse avancée", key="advanced_ai_analyze"):
            if custom_question and st.session_state.get('search_results'):
                # Analyser avec les IA sélectionnées
                st.info("🔄 Analyse avancée en cours...")
            else:
                st.warning("⚠️ Veuillez saisir une question et avoir des documents")
    else:
        st.error("❌ Aucune IA disponible")