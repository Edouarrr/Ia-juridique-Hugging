# modules/recherche_simplified.py
"""Module de recherche universelle simplifié - Sans redondances"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

# ========================= CONFIGURATION =========================

# Import des modules existants au lieu de dupliquer le code
try:
    # VOS MODULES RÉELS
    from modules.analyse_ia import show_page as analyse_ia_page
    from modules.bordereau import process_bordereau_request, create_bordereau
    from modules.comparison import process_comparison_request
    from modules.configuration import show_page as config_page
    from modules.email import process_email_request
    from modules.explorer import show_explorer_interface
    from modules.import_export import process_import_request, process_export_request
    from modules.jurisprudence import process_jurisprudence_request, show_jurisprudence_interface
    from modules.mapping import process_mapping_request
    from modules.plaidoirie import process_plaidoirie_request
    from modules.preparation_client import process_preparation_client_request
    from modules.redaction_unified import process_redaction_request
    from modules.selection_piece import show_page as selection_piece_page
    from modules.synthesis import process_synthesis_request
    from modules.templates import process_template_request
    from modules.timeline import process_timeline_request
    
    # Managers
    from managers.universal_search_service import UniversalSearchService
    from managers.multi_llm_manager import MultiLLMManager
    
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Modules manquants : {e}")
    MODULES_AVAILABLE = False

# ========================= PAGE PRINCIPALE =========================

def show_page():
    """Page principale de recherche universelle"""
    
    st.markdown("## 🔍 Recherche Universelle")
    
    # Barre de recherche principale
    col1, col2 = st.columns([5, 1])
    
    with col1:
        query = st.text_input(
            "Entrez votre commande ou recherche",
            placeholder="Ex: rédiger plainte contre X, analyser @dossier, créer bordereau...",
            key="universal_query",
            help="Utilisez @ pour référencer une affaire spécifique"
        )
    
    with col2:
        search_button = st.button("🔍 Rechercher", type="primary", use_container_width=True)
    
    # Suggestions
    show_command_suggestions()
    
    # Actions rapides
    show_quick_actions()
    
    # Traiter la requête
    if query and search_button:
        process_query(query)
    
    # Afficher les résultats s'il y en a
    show_results()

# ========================= TRAITEMENT SIMPLIFIÉ =========================

def process_query(query: str):
    """Traite la requête et route vers le bon module"""
    
    with st.spinner("🔄 Analyse de votre demande..."):
        # Analyser la requête
        query_lower = query.lower()
        
        # Router vers le bon module selon les mots-clés
        if any(word in query_lower for word in ['plainte', 'porter plainte']):
            handle_plainte_request(query)
            
        elif any(word in query_lower for word in ['rédiger', 'créer', 'écrire']):
            if MODULES_AVAILABLE:
                process_redaction_request(query, {})
            else:
                st.error("Module de rédaction non disponible")
                
        elif any(word in query_lower for word in ['analyser', 'analyse', 'risques']):
            handle_analysis_request(query)
            
        elif 'bordereau' in query_lower:
            if MODULES_AVAILABLE:
                process_bordereau_request(query, {})
            else:
                st.error("Module bordereau non disponible")
                
        elif any(word in query_lower for word in ['importer', 'import', 'charger']):
            if MODULES_AVAILABLE:
                process_import_request(query, {})
            else:
                handle_import_fallback()
                
        elif any(word in query_lower for word in ['exporter', 'export', 'télécharger']):
            if MODULES_AVAILABLE:
                process_export_request(query, {})
            else:
                st.error("Module export non disponible")
                
        elif 'jurisprudence' in query_lower:
            if MODULES_AVAILABLE:
                process_jurisprudence_request(query, {})
            else:
                st.error("Module jurisprudence non disponible")
                
        elif any(word in query_lower for word in ['plaidoirie', 'plaider', 'audience']):
            if MODULES_AVAILABLE:
                process_plaidoirie_request(query, {})
            else:
                st.error("Module plaidoirie non disponible")
                
        elif any(word in query_lower for word in ['préparer client', 'préparation client', 'interrogatoire']):
            if MODULES_AVAILABLE:
                process_preparation_client_request(query, {})
            else:
                st.error("Module préparation client non disponible")
                
        elif any(word in query_lower for word in ['chronologie', 'timeline']):
            if MODULES_AVAILABLE:
                process_timeline_request(query, {})
            else:
                st.error("Module timeline non disponible")
                
        elif any(word in query_lower for word in ['cartographie', 'mapping', 'carte']):
            if MODULES_AVAILABLE:
                process_mapping_request(query, {})
            else:
                st.error("Module mapping non disponible")
                
        elif 'comparer' in query_lower:
            if MODULES_AVAILABLE:
                process_comparison_request(query, {})
            else:
                st.error("Module comparaison non disponible")
                
        elif any(word in query_lower for word in ['sélectionner', 'sélection', 'pièces']):
            if MODULES_AVAILABLE:
                selection_piece_page()
            else:
                st.error("Module sélection non disponible")
        
        elif any(word in query_lower for word in ['explorer', 'parcourir', 'fichiers']):
            if MODULES_AVAILABLE:
                show_explorer_interface()
            else:
                st.error("Module explorer non disponible")
                
        elif any(word in query_lower for word in ['synthèse', 'synthétiser', 'résumer']):
            if MODULES_AVAILABLE:
                process_synthesis_request(query, {})
            else:
                st.error("Module synthèse non disponible")
                
        elif any(word in query_lower for word in ['template', 'modèle']):
            if MODULES_AVAILABLE:
                process_template_request(query, {})
            else:
                st.error("Module templates non disponible")
                
        elif any(word in query_lower for word in ['configuration', 'paramètres', 'configurer']):
            if MODULES_AVAILABLE:
                config_page()
            else:
                st.error("Module configuration non disponible")
                
        elif 'email' in query_lower or 'envoyer' in query_lower:
            if MODULES_AVAILABLE:
                process_email_request(query, {})
            else:
                st.error("Module email non disponible")
                
        else:
            # Recherche simple par défaut
            handle_search_request(query)

# ========================= HANDLERS SPÉCIFIQUES =========================

def handle_plainte_request(query: str):
    """Gère les demandes de plainte de manière simplifiée"""
    
    st.info("📝 Création de plainte détectée")
    
    # Extraire les informations basiques
    query_lower = query.lower()
    is_cpc = 'partie civile' in query_lower or 'cpc' in query_lower
    
    # Interface simple
    with st.form("plainte_form"):
        st.markdown("### 📋 Informations pour la plainte")
        
        col1, col2 = st.columns(2)
        
        with col1:
            plaignants = st.text_area(
                "Plaignants (un par ligne)",
                placeholder="Société X\nM. Dupont",
                height=100
            )
            
            type_plainte = st.radio(
                "Type de plainte",
                ["Plainte simple", "Plainte avec constitution de partie civile"],
                index=1 if is_cpc else 0
            )
        
        with col2:
            mis_en_cause = st.text_area(
                "Mis en cause (un par ligne)",
                placeholder="M. Martin\nSociété Y",
                height=100
            )
            
            infractions = st.multiselect(
                "Infractions",
                ["Escroquerie", "Abus de confiance", "Abus de biens sociaux", 
                 "Faux et usage de faux", "Corruption", "Blanchiment"],
                default=["Escroquerie", "Abus de confiance"]
            )
        
        contexte = st.text_area(
            "Contexte des faits",
            placeholder="Décrivez brièvement les faits...",
            height=150
        )
        
        if st.form_submit_button("🚀 Générer la plainte", type="primary"):
            generate_simple_plainte(
                plaignants.split('\n') if plaignants else [],
                mis_en_cause.split('\n') if mis_en_cause else [],
                infractions,
                type_plainte,
                contexte
            )

def generate_simple_plainte(plaignants, mis_en_cause, infractions, type_plainte, contexte):
    """Génère une plainte en utilisant les fonctionnalités avancées si disponibles"""
    
    # Utiliser le MultiLLMManager si disponible
    try:
        llm_manager = MultiLLMManager()
        
        if not llm_manager.clients:
            st.error("❌ Aucune IA configurée. Veuillez ajouter une clé API.")
            return
        
        # Déterminer si c'est une CPC
        is_cpc = "partie civile" in type_plainte.lower()
        
        # Si les fonctionnalités avancées sont disponibles, les utiliser
        if ADVANCED_FEATURES:
            with st.spinner("⚖️ Génération avancée en cours..."):
                result = generate_advanced_plainte(
                    query=contexte,
                    parties_demanderesses=plaignants,
                    parties_defenderesses=mis_en_cause,
                    infractions=infractions,
                    is_partie_civile=is_cpc,
                    reference=None,
                    modele=None,
                    llm_manager=llm_manager
                )
                
                if result['success']:
                    st.session_state.generated_plainte = result['document']
                    st.success("✅ Plainte générée avec succès (mode avancé) !")
                    
                    # Afficher les suggestions d'amélioration
                    if 'improvement_suggestions' in result:
                        with st.expander("💡 Suggestions d'amélioration"):
                            for suggestion in result['improvement_suggestions']:
                                st.write(suggestion)
                    
                    # Afficher la vérification des jurisprudences
                    if 'jurisprudence_verification' in result and result['jurisprudence_verification'].get('available'):
                        with st.expander("🔍 Vérification des jurisprudences"):
                            stats = result['jurisprudence_verification']['statistics']
                            st.metric("Jurisprudences vérifiées", f"{stats['verified']}/{stats['total']}")
                            st.metric("Fiabilité", f"{stats['confidence']:.0f}%")
                else:
                    st.error(f"❌ Erreur : {result.get('error', 'Erreur inconnue')}")
        else:
            # Fallback au mode simple
            prompt = f"""Rédige une {type_plainte} complète et professionnelle.

PLAIGNANTS : {', '.join(plaignants)}
MIS EN CAUSE : {', '.join(mis_en_cause)}
INFRACTIONS : {', '.join(infractions)}
CONTEXTE : {contexte}

Structure attendue :
1. En-tête (Procureur ou Doyen selon le type)
2. Identité des plaignants
3. Exposé détaillé des faits
4. Qualification juridique
5. Préjudices subis
6. {"Constitution de partie civile et demandes" if is_cpc else "Demandes"}
7. Liste des pièces

Rédige de manière complète et professionnelle (minimum 3000 mots)."""

            # Générer
            with st.spinner("⚖️ Génération en cours..."):
                provider = list(llm_manager.clients.keys())[0]
                response = llm_manager.query_single_llm(
                    provider,
                    prompt,
                    "Tu es un avocat expert en droit pénal."
                )
                
                if response['success']:
                    st.session_state.generated_plainte = response['response']
                    st.success("✅ Plainte générée avec succès !")
                else:
                    st.error(f"❌ Erreur : {response.get('error')}")
                
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")

def handle_analysis_request(query: str):
    """Gère les demandes d'analyse"""
    
    if MODULES_AVAILABLE:
        # Utiliser le module analyse_ia existant
        analyse_ia_page()
    else:
        st.info("🤖 Analyse simple")
        
        # Interface basique
        analysis_type = st.selectbox(
            "Type d'analyse",
            ["Risques juridiques", "Conformité", "Stratégie", "Générale"]
        )
        
        if st.button("Lancer l'analyse"):
            st.info("Analyse en cours...")
            # TODO: Implémenter une analyse simple

def handle_search_request(query: str):
    """Gère les recherches simples"""
    
    st.info(f"🔍 Recherche : {query}")
    
    # Recherche dans les documents locaux
    results = search_local_documents(query)
    
    if results:
        st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
        
        for i, result in enumerate(results[:10], 1):
            with st.expander(f"{i}. {result['title']}"):
                st.write(result.get('content', '')[:500] + "...")
    else:
        st.warning("❌ Aucun résultat trouvé")

def handle_import_fallback():
    """Import simple sans module dédié"""
    
    st.info("📥 Import de documents")
    
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Importer"):
        for file in uploaded_files:
            # Stocker simplement le fichier
            if 'imported_files' not in st.session_state:
                st.session_state.imported_files = {}
            
            st.session_state.imported_files[file.name] = {
                'name': file.name,
                'size': file.size,
                'type': file.type
            }
            
            st.success(f"✅ {file.name} importé")

# ========================= AFFICHAGE DES RÉSULTATS =========================

def show_results():
    """Affiche les résultats selon leur type"""
    
    # Plainte générée
    if st.session_state.get('generated_plainte'):
        st.markdown("### 📋 Plainte générée")
        
        content = st.text_area(
            "Contenu",
            value=st.session_state.generated_plainte,
            height=600,
            key="plainte_content"
        )
        
        # Barre d'outils
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.download_button(
                "📥 Télécharger (.txt)",
                content,
                f"plainte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain"
            )
        
        with col2:
            if st.button("🗑️ Effacer"):
                del st.session_state.generated_plainte
                st.rerun()
        
        with col3:
            # Vérifier les jurisprudences si disponible
            if ADVANCED_FEATURES and st.button("🔍 Vérifier jurisprudences"):
                verify_jurisprudences_in_analysis(content)
        
        with col4:
            # Comparer avec d'autres IA si disponible
            if ADVANCED_FEATURES and st.button("🤖 Comparer IA"):
                try:
                    llm_manager = MultiLLMManager()
                    if llm_manager.clients:
                        with st.spinner("Comparaison en cours..."):
                            # Créer un prompt court pour la comparaison
                            short_prompt = "Rédige une plainte simple pour escroquerie."
                            results = compare_all_providers(short_prompt, llm_manager)
                            
                            if results and not results.get('error'):
                                st.success(f"✅ Comparé {len(results)} providers")
                except Exception as e:
                    st.error(f"Erreur comparaison : {e}")
    
    # Autres résultats...
    # Ajouter ici l'affichage d'autres types de résultats

# ========================= INTERFACE UTILISATEUR =========================

def show_command_suggestions():
    """Affiche les suggestions de commandes"""
    
    with st.expander("💡 Exemples de commandes"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📝 Rédaction :**
            - `rédiger plainte contre X pour escroquerie`
            - `créer conclusions de défense`
            - `rédiger mise en demeure`
            
            **🤖 Analyse :**
            - `analyser les risques du dossier`
            - `identifier les infractions`
            - `analyser la conformité`
            """)
        
        with col2:
            st.markdown("""
            **📋 Gestion :**
            - `créer bordereau`
            - `importer documents`
            - `sélectionner pièces`
            - `explorer fichiers`
            
            **🔍 Recherche :**
            - `jurisprudence abus de biens sociaux`
            - `rechercher contrats 2024`
            """)
            
        with col3:
            st.markdown("""
            **🎯 Spécialisé :**
            - `préparer plaidoirie`
            - `préparer client pour interrogatoire`
            - `créer chronologie`
            - `cartographie des relations`
            - `comparer documents`
            - `synthétiser pièces`
            """)

def show_quick_actions():
    """Affiche les boutons d'actions rapides"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Nouvelle plainte", use_container_width=True):
            st.session_state.universal_query = "rédiger plainte"
            st.rerun()
    
    with col2:
        if st.button("🤖 Analyser", use_container_width=True):
            st.session_state.universal_query = "analyser dossier"
            st.rerun()
    
    with col3:
        if st.button("📥 Importer", use_container_width=True):
            st.session_state.universal_query = "importer documents"
            st.rerun()
    
    with col4:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith('generated_') or key == 'universal_query':
                    del st.session_state[key]
            st.rerun()
    
    # Deuxième ligne d'actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚖️ Jurisprudence", use_container_width=True):
            if MODULES_AVAILABLE:
                show_jurisprudence_interface()
    
    with col2:
        if st.button("📁 Explorer", use_container_width=True):
            if MODULES_AVAILABLE:
                show_explorer_interface()
    
    with col3:
        if st.button("📋 Bordereau", use_container_width=True):
            st.session_state.universal_query = "créer bordereau"
            st.rerun()
    
    with col4:
        if st.button("⚙️ Configuration", use_container_width=True):
            if MODULES_AVAILABLE:
                config_page()

# ========================= FONCTIONS UTILITAIRES =========================

def search_local_documents(query: str) -> list:
    """Recherche simple dans les documents locaux"""
    
    results = []
    query_lower = query.lower()
    
    # Rechercher dans azure_documents
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        if hasattr(doc, 'title') and hasattr(doc, 'content'):
            if query_lower in doc.title.lower() or query_lower in doc.content.lower():
                results.append({
                    'id': doc_id,
                    'title': doc.title,
                    'content': doc.content,
                    'source': getattr(doc, 'source', 'Local')
                })
    
    return results

# ========================= POINT D'ENTRÉE =========================

if __name__ == "__main__":
    show_page()