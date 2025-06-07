# pages/redaction_assistee.py
"""Page de rédaction assistée"""

import streamlit as st
import asyncio
import io
import json
from datetime import datetime

from config.app_config import InfractionAffaires
from managers.multi_llm_manager import MultiLLMManager
from managers.style_analyzer import StyleAnalyzer
from managers.dynamic_generators import generate_dynamic_templates
from utils.helpers import clean_key, merge_structures, merge_formules, merge_formatting, merge_vocabulary

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

def show_page():
    """Affiche la page de rédaction assistée"""
    st.header("📝 Rédaction assistée par IA")
    
    # Boutons d'accès rapide
    show_quick_actions()
    
    # Onglets
    tabs = st.tabs(["✍️ Rédaction", "🎨 Apprentissage de style", "📚 Modèles"])
    
    with tabs[0]:
        show_redaction_tab()
    
    with tabs[1]:
        show_style_learning_tab()
    
    with tabs[2]:
        show_templates_tab()

def show_quick_actions():
    """Affiche les boutons d'accès rapide"""
    st.markdown("### ⚡ Accès rapide")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📜 Créer des conclusions", key="quick_conclusions", use_container_width=True):
            st.session_state.type_acte_input = "Conclusions"
            st.session_state.quick_action = "conclusions"
    
    with col2:
        if st.button("⚖️ Créer une plainte simple", key="quick_plainte_simple", use_container_width=True):
            st.session_state.type_acte_input = "Plainte simple"
            st.session_state.quick_action = "plainte_simple"
    
    with col3:
        if st.button("🏛️ Plainte avec constitution PC", key="quick_plainte_pc", use_container_width=True):
            st.session_state.type_acte_input = "Plainte avec constitution de partie civile"
            st.session_state.quick_action = "plainte_pc"
    
    # Auto-apprentissage si action rapide
    if 'quick_action' in st.session_state and st.session_state.quick_action:
        show_auto_learn_suggestion()

def show_auto_learn_suggestion():
    """Suggère l'apprentissage automatique de style"""
    st.info(f"💡 Mode rapide : {st.session_state.type_acte_input}")
    
    if st.button("🎓 Apprendre le style depuis mes modèles SharePoint", key="auto_learn_style"):
        with st.spinner("Recherche et analyse des modèles dans SharePoint..."):
            learn_style_from_sharepoint()

def learn_style_from_sharepoint():
    """Apprend le style depuis les documents SharePoint"""
    modeles_trouves = []
    
    # Parcourir les documents SharePoint
    for doc_id, doc in st.session_state.azure_documents.items():
        doc_title_lower = doc.title.lower()
        
        # Identifier les modèles selon le type d'acte
        if st.session_state.quick_action == "conclusions":
            if any(term in doc_title_lower for term in ["conclusion", "mémoire", "réponse"]):
                modeles_trouves.append(doc)
        elif st.session_state.quick_action == "plainte_simple":
            if "plainte" in doc_title_lower and "constitution" not in doc_title_lower:
                modeles_trouves.append(doc)
        elif st.session_state.quick_action == "plainte_pc":
            if "plainte" in doc_title_lower and "constitution" in doc_title_lower:
                modeles_trouves.append(doc)
    
    if modeles_trouves:
        st.success(f"✅ {len(modeles_trouves)} modèles trouvés !")
        
        # Analyser automatiquement
        if 'style_analyzer' not in st.session_state:
            st.session_state.style_analyzer = StyleAnalyzer()
        
        patterns = []
        for doc in modeles_trouves[:5]:  # Limiter à 5 modèles
            pattern = st.session_state.style_analyzer.analyze_document(doc, st.session_state.type_acte_input)
            patterns.append(pattern)
            st.caption(f"✓ {doc.title} analysé")
        
        # Fusionner et sauvegarder
        merged_pattern = {
            'nombre_documents': len(patterns),
            'structure_commune': merge_structures([p.structure for p in patterns]),
            'formules_frequentes': merge_formules([p.formules for p in patterns]),
            'mise_en_forme_type': merge_formatting([p.mise_en_forme for p in patterns]),
            'vocabulaire_cle': merge_vocabulary([p.vocabulaire for p in patterns])
        }
        
        if 'learned_styles' not in st.session_state:
            st.session_state.learned_styles = {}
        
        style_name = f"Style {st.session_state.type_acte_input} (auto)"
        st.session_state.learned_styles[style_name] = merged_pattern
        st.session_state.auto_learned_style = style_name
        
        st.success(f"🎨 Style appris et prêt à être utilisé !")
        
        # Afficher un aperçu
        with st.expander("Aperçu du style appris"):
            st.write("**Structure identifiée :**")
            for section in merged_pattern['structure_commune'].get('sections_communes', [])[:5]:
                st.write(f"- {section}")
            
            st.write("\n**Formules types détectées :**")
            for formule in merged_pattern['formules_frequentes'][:5]:
                st.write(f"- {formule[:100]}...")
    else:
        st.warning("⚠️ Aucun modèle trouvé dans SharePoint.")

def show_redaction_tab():
    """Affiche l'onglet de rédaction"""
    st.markdown("### 📄 Créer un nouvel acte")
    
    # Type d'acte
    col1, col2 = st.columns([2, 1])
    
    with col1:
        default_type = st.session_state.get('type_acte_input', '')
        
        type_acte = st.text_input(
            "Type d'acte à rédiger",
            value=default_type,
            placeholder="Ex: Plainte avec constitution de partie civile, Conclusions...",
            key="type_acte_input_field"
        )
    
    with col2:
        # Utiliser un style appris
        if 'learned_styles' in st.session_state and st.session_state.learned_styles:
            use_style = st.checkbox(
                "Utiliser un style appris", 
                value='auto_learned_style' in st.session_state,
                key="use_learned_style"
            )
        else:
            use_style = False
            st.info("Aucun style appris")
    
    # Sélection du style
    selected_style = None
    if use_style and st.session_state.learned_styles:
        default_style_idx = 0
        if 'auto_learned_style' in st.session_state:
            style_list = list(st.session_state.learned_styles.keys())
            if st.session_state.auto_learned_style in style_list:
                default_style_idx = style_list.index(st.session_state.auto_learned_style)
        
        selected_style = st.selectbox(
            "Choisir un style",
            list(st.session_state.learned_styles.keys()),
            index=default_style_idx,
            key="select_style_redaction"
        )
    
    # Informations spécifiques selon le type
    if type_acte:
        show_specific_form(type_acte)
    
    # Options de génération
    show_generation_options()
    
    # Bouton de génération
    if st.button("🚀 Générer l'acte", type="primary", key="generer_acte"):
        generate_document(type_acte, selected_style)

def show_specific_form(type_acte):
    """Affiche le formulaire spécifique selon le type d'acte"""
    if "plainte" in type_acte.lower():
        show_plainte_form(type_acte)
    elif "conclusion" in type_acte.lower():
        show_conclusions_form()
    else:
        show_generic_form()

def show_plainte_form(type_acte):
    """Affiche le formulaire pour une plainte"""
    st.markdown("#### 📋 Informations pour la plainte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.plaignant = st.text_input("Plaignant (votre client)", key="plaignant_nom")
        st.session_state.qualite_plaignant = st.text_input("Qualité du plaignant", key="plaignant_qualite")
        
        if "constitution" in type_acte.lower():
            st.session_state.avocat_nom = st.text_input("Avocat", placeholder="Maître...", key="avocat_plainte")
            st.session_state.constitution_pc = st.checkbox("Demander des dommages-intérêts", value=True, key="demande_di")
    
    with col2:
        st.session_state.mis_en_cause = st.text_input("Personne(s) mise(s) en cause", key="mis_en_cause")
        st.session_state.faits_date = st.date_input("Date des faits", key="date_faits_plainte")
        st.session_state.juridiction = st.text_input(
            "Juridiction compétente",
            value="Tribunal judiciaire de Paris - Pôle économique et financier",
            key="juridiction_plainte"
        )
    
    # Infractions
    st.session_state.infractions = st.multiselect(
        "Infractions visées",
        [inf.value for inf in InfractionAffaires],
        key="infractions_plainte"
    )
    
    # Résumé des faits
    st.session_state.resume_faits = st.text_area(
        "Résumé des faits",
        placeholder="Décrivez brièvement les faits reprochés...",
        height=150,
        key="resume_faits_plainte"
    )

def show_conclusions_form():
    """Affiche le formulaire pour des conclusions"""
    st.markdown("#### 📋 Informations pour les conclusions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.client_nom = st.text_input("Client défendu", key="client_conclusions")
        st.session_state.numero_procedure = st.text_input("N° de procédure", key="num_procedure")
        st.session_state.juridiction = st.text_input("Juridiction", key="juridiction_conclusions")
    
    with col2:
        st.session_state.partie_adverse = st.text_input("Partie adverse", key="partie_adverse")
        st.session_state.date_audience = st.date_input("Date d'audience", key="date_audience")
        st.session_state.type_conclusions = st.selectbox(
            "Type de conclusions",
            ["Conclusions en défense", "Conclusions en demande", "Conclusions récapitulatives"],
            key="type_conclusions_select"
        )
    
    # Moyens
    st.session_state.moyens = st.text_area(
        "Moyens principaux",
        placeholder="""Ex:
- Sur la prescription des faits
- Sur l'absence d'élément intentionnel
- Sur le défaut de préjudice""",
        height=150,
        key="moyens_conclusions"
    )

def show_generic_form():
    """Affiche un formulaire générique"""
    st.markdown("### 📋 Informations essentielles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.destinataire = st.text_input("Destinataire", key="destinataire_acte")
        st.session_state.client_nom = st.text_input("Client", key="client_nom_acte")
        st.session_state.avocat_nom = st.text_input("Avocat", key="avocat_nom_acte")
    
    with col2:
        st.session_state.reference = st.text_input("Référence", key="reference_acte")
        st.session_state.infraction = st.text_input("Infraction(s)", key="infraction_acte")
        st.session_state.date_faits = st.date_input("Date des faits", key="date_faits_acte")

def show_generation_options():
    """Affiche les options de génération"""
    st.markdown("### 📝 Points clés à développer")
    
    st.session_state.points_cles = st.text_area(
        "Points clés",
        placeholder="""Ex:
- Absence d'élément intentionnel
- Actions réalisées dans l'intérêt de la société
- Bonne foi du dirigeant
- Préjudice non caractérisé""",
        height=150,
        key="points_cles_acte"
    )
    
    # Pièces à mentionner
    if st.session_state.pieces_selectionnees:
        st.markdown("#### 📎 Pièces à citer")
        
        st.session_state.pieces_a_citer = []
        for piece_id, piece in st.session_state.pieces_selectionnees.items():
            if st.checkbox(
                f"Pièce n°{len(st.session_state.pieces_a_citer)+1} : {piece.titre}",
                key=f"cite_piece_{piece_id}"
            ):
                st.session_state.pieces_a_citer.append(piece)
    
    # Options de style
    st.markdown("### ⚙️ Options de génération")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.session_state.ton = st.select_slider(
            "Ton",
            options=["Très formel", "Formel", "Neutre", "Direct", "Combatif"],
            value="Formel",
            key="ton_generation"
        )
    
    with col2:
        st.session_state.longueur = st.select_slider(
            "Longueur",
            options=["Concis", "Standard", "Détaillé", "Très détaillé"],
            value="Standard",
            key="longueur_generation"
        )
    
    with col3:
        st.session_state.inclure_jurisprudence = st.checkbox(
            "Inclure des références jurisprudentielles",
            value=True,
            key="inclure_juris"
        )

def generate_document(type_acte, selected_style):
    """Génère le document avec l'IA"""
    if not type_acte:
        st.error("❌ Veuillez spécifier le type d'acte")
        return
    
    # Construire le prompt
    prompt = build_generation_prompt(type_acte)
    
    # Si un style est sélectionné, l'ajouter
    if selected_style and selected_style in st.session_state.learned_styles:
        style_info = st.session_state.learned_styles[selected_style]
        prompt += f"\n\nApplique le style suivant :\n{json.dumps(style_info, ensure_ascii=False, indent=2)}"
    
    # Générer avec l'IA
    llm_manager = MultiLLMManager()
    
    with st.spinner("🔄 Génération en cours..."):
        if llm_manager.clients:
            provider = list(llm_manager.clients.keys())[0]
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(
                llm_manager.query_single_llm(
                    provider,
                    prompt,
                    "Tu es un avocat spécialisé en droit pénal des affaires, expert en rédaction d'actes juridiques."
                )
            )
            
            if response['success']:
                # Appliquer le style si nécessaire
                contenu_genere = response['response']
                
                if selected_style and 'style_analyzer' in st.session_state:
                    contenu_genere = st.session_state.style_analyzer.generate_with_style(
                        selected_style,
                        contenu_genere
                    )
                
                # Afficher le résultat
                show_generated_document(contenu_genere, type_acte)
            else:
                st.error(f"❌ Erreur : {response['error']}")
        else:
            st.error("❌ Aucune IA disponible")

def build_generation_prompt(type_acte):
    """Construit le prompt de génération selon le type d'acte"""
    if "plainte" in type_acte.lower():
        return build_plainte_prompt(type_acte)
    elif "conclusion" in type_acte.lower():
        return build_conclusions_prompt(type_acte)
    else:
        return build_generic_prompt(type_acte)

def build_plainte_prompt(type_acte):
    """Construit le prompt pour une plainte"""
    prompt = f"""Tu es un avocat expert en droit pénal des affaires.
Rédige une {type_acte} avec les informations suivantes :
Plaignant : {st.session_state.get('plaignant', 'Non spécifié')}
Qualité : {st.session_state.get('qualite_plaignant', 'Non spécifiée')}
{"Avocat : " + st.session_state.get('avocat_nom', '') if st.session_state.get('avocat_nom') else ""}
Mis en cause : {st.session_state.get('mis_en_cause', 'Non spécifié')}
Date des faits : {st.session_state.get('faits_date', 'Non spécifiée')}
Juridiction : {st.session_state.get('juridiction', 'Non spécifiée')}
Infractions : {', '.join(st.session_state.get('infractions', [])) if st.session_state.get('infractions') else 'Non spécifiées'}
Résumé des faits :
{st.session_state.get('resume_faits', 'Non fourni')}
{"Avec constitution de partie civile et demande de dommages-intérêts" if st.session_state.get('constitution_pc') else ""}
Points clés supplémentaires :
{st.session_state.get('points_cles', '')}"""
    
    return prompt + build_common_prompt_suffix()

def build_conclusions_prompt(type_acte):
    """Construit le prompt pour des conclusions"""
    prompt = f"""Tu es un avocat expert en droit pénal des affaires.
Rédige des {type_acte} avec les informations suivantes :
Type : {st.session_state.get('type_conclusions', 'Conclusions')}
Client : {st.session_state.get('client_nom', 'Non spécifié')}
Procédure n° : {st.session_state.get('numero_procedure', 'Non spécifié')}
Juridiction : {st.session_state.get('juridiction', 'Non spécifiée')}
Partie adverse : {st.session_state.get('partie_adverse', 'Non spécifiée')}
Audience : {st.session_state.get('date_audience', 'Non spécifiée')}
Moyens développés :
{st.session_state.get('moyens', st.session_state.get('points_cles', ''))}"""
    
    return prompt + build_common_prompt_suffix()

def build_generic_prompt(type_acte):
    """Construit un prompt générique"""
    prompt = f"""Tu es un avocat expert en droit pénal des affaires.
Rédige un(e) {type_acte} avec les informations suivantes :
Destinataire : {st.session_state.get('destinataire', 'Non spécifié')}
Client : {st.session_state.get('client_nom', 'Non spécifié')}
Avocat : {st.session_state.get('avocat_nom', 'Non spécifié')}
Référence : {st.session_state.get('reference', 'Non spécifiée')}
Infraction(s) : {st.session_state.get('infraction', 'Non spécifiée')}
Date des faits : {st.session_state.get('date_faits', 'Non spécifiée')}
Points clés à développer :
{st.session_state.get('points_cles', '')}"""
    
    return prompt + build_common_prompt_suffix()

def build_common_prompt_suffix():
    """Construit la partie commune du prompt"""
    suffix = f"""
Ton souhaité : {st.session_state.get('ton', 'Formel')}
Longueur : {st.session_state.get('longueur', 'Standard')}
{"Inclure des références jurisprudentielles pertinentes" if st.session_state.get('inclure_jurisprudence') else ""}
Structure l'acte de manière professionnelle avec :
- Un en-tête approprié
- Une introduction claire
- Un développement structuré des arguments
- Une conclusion percutante
- Les formules de politesse adaptées"""
    
    if st.session_state.get('pieces_a_citer'):
        pieces_str = ", ".join([f"Pièce n°{i+1} : {p.titre}" for i, p in enumerate(st.session_state.pieces_a_citer)])
        suffix += f"\nCite les pièces suivantes : {pieces_str}"
    
    return suffix

def show_generated_document(contenu_genere, type_acte):
    """Affiche le document généré"""
    st.markdown("### 📄 Acte généré")
    
    st.text_area(
        "Contenu",
        value=contenu_genere,
        height=600,
        key="acte_genere_content"
    )
    
    # Options d'export
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "💾 Télécharger (.txt)",
            contenu_genere,
            f"{clean_key(type_acte)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "text/plain",
            key="download_txt_acte"
        )
    
    with col2:
        if DOCX_AVAILABLE:
            # Créer un document Word
            doc = DocxDocument()
            
            for paragraph in contenu_genere.split('\n'):
                doc.add_paragraph(paragraph)
            
            # Sauvegarder en mémoire
            docx_buffer = io.BytesIO()
            doc.save(docx_buffer)
            docx_buffer.seek(0)
            
            st.download_button(
                "💾 Télécharger (.docx)",
                docx_buffer.getvalue(),
                f"{clean_key(type_acte)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_docx_acte"
            )
    
    with col3:
        if st.button("📧 Préparer l'envoi", key="prepare_send"):
            st.info("Fonctionnalité d'envoi à implémenter")

def show_style_learning_tab():
    """Affiche l'onglet d'apprentissage de style"""
    st.markdown("### 🎨 Apprendre un style de rédaction")
    
    st.info("""
    Cette fonctionnalité analyse vos documents modèles pour apprendre votre style de rédaction :
    - Structure des documents
    - Formules types utilisées
    - Mise en forme préférée
    - Vocabulaire spécifique
    
    **Nouveauté** : Vous pouvez maintenant analyser des documents Word (.docx) directement !
    """)
    
    # Type d'acte pour le style
    type_style = st.text_input(
        "Nom du style à apprendre",
        placeholder="Ex: Plainte pénale, Conclusions de relaxe...",
        key="type_style_learn"
    )
    
    # Apprentissage automatique depuis SharePoint
    if st.button("🎓 Apprendre automatiquement depuis SharePoint", key="auto_learn_from_sharepoint"):
        if not type_style:
            st.error("❌ Veuillez spécifier un nom de style")
        else:
            with st.spinner("Recherche de modèles dans SharePoint..."):
                # Rechercher les documents pertinents
                modeles_auto = []
                
                for doc_id, doc in st.session_state.azure_documents.items():
                    doc_title_lower = doc.title.lower()
                    type_style_lower = type_style.lower()
                    
                    # Recherche intelligente de modèles
                    if any(term in type_style_lower for term in ["plainte", "conclusion", "mémoire", "demande", "requête"]):
                        if any(term in doc_title_lower for term in type_style_lower.split()):
                            modeles_auto.append(doc)
                
                if modeles_auto:
                    st.success(f"✅ {len(modeles_auto)} modèles potentiels trouvés")
                    
                    # Analyser automatiquement
                    if st.button("Analyser ces modèles", key="analyze_auto_models"):
                        if 'style_analyzer' not in st.session_state:
                            st.session_state.style_analyzer = StyleAnalyzer()
                        
                        patterns = []
                        for doc in modeles_auto[:10]:  # Limiter à 10
                            pattern = st.session_state.style_analyzer.analyze_document(doc, type_style)
                            patterns.append(pattern)
                            st.caption(f"✓ {doc.title} analysé")
                        
                        # Fusionner et sauvegarder
                        merged_pattern = {
                            'nombre_documents': len(patterns),
                            'structure_commune': merge_structures([p.structure for p in patterns]),
                            'formules_frequentes': merge_formules([p.formules for p in patterns]),
                            'mise_en_forme_type': merge_formatting([p.mise_en_forme for p in patterns]),
                            'vocabulaire_cle': merge_vocabulary([p.vocabulaire for p in patterns])
                        }
                        
                        if 'learned_styles' not in st.session_state:
                            st.session_state.learned_styles = {}
                        
                        st.session_state.learned_styles[type_style] = merged_pattern
                        
                        st.success(f"✅ Style '{type_style}' appris avec succès!")
                        
                        # Afficher un résumé
                        with st.expander("Voir le résumé du style appris"):
                            st.json(merged_pattern)
                else:
                    st.warning("⚠️ Aucun modèle trouvé. Essayez avec un nom plus précis.")
    
    # Sélection manuelle des documents
    if st.session_state.azure_documents:
        st.markdown("#### 📚 Ou sélectionner manuellement les documents modèles")
        
        # Sélection des documents
        docs_modeles = []
        for doc_id, doc in st.session_state.azure_documents.items():
            if st.checkbox(
                f"{doc.title}",
                key=f"model_{doc_id}",
                help=f"Source: {doc.source}"
            ):
                docs_modeles.append(doc)
    
    # Upload de documents Word
    st.markdown("#### 📤 Ou télécharger des documents Word")
    
    uploaded_files = st.file_uploader(
        "Choisir des fichiers Word (.docx)",
        type=['docx'],
        accept_multiple_files=True,
        key="upload_word_models"
    )
    
    if st.button("🧠 Apprendre le style", key="learn_style") and type_style:
        if not docs_modeles and not uploaded_files:
            st.error("❌ Veuillez sélectionner au moins un document modèle")
            return
        
        with st.spinner("Analyse en cours..."):
            # Initialiser l'analyseur
            if 'style_analyzer' not in st.session_state:
                st.session_state.style_analyzer = StyleAnalyzer()
            
            patterns = []
            
            # Analyser les documents Azure
            for doc in docs_modeles:
                pattern = st.session_state.style_analyzer.analyze_document(doc, type_style)
                patterns.append(pattern)
            
            # Analyser les documents Word uploadés
            if uploaded_files and DOCX_AVAILABLE:
                for uploaded_file in uploaded_files:
                    # Lire le contenu du fichier
                    doc_bytes = uploaded_file.read()
                    
                    # Analyser le document Word
                    pattern = st.session_state.style_analyzer.analyze_word_document(doc_bytes, type_style)
                    if pattern:
                        patterns.append(pattern)
                        st.success(f"✅ {uploaded_file.name} analysé")
            
            if patterns:
                # Fusionner les patterns
                merged_pattern = {
                    'nombre_documents': len(patterns),
                    'structure_commune': merge_structures([p.structure for p in patterns]),
                    'formules_frequentes': merge_formules([p.formules for p in patterns]),
                    'mise_en_forme_type': merge_formatting([p.mise_en_forme for p in patterns]),
                    'vocabulaire_cle': merge_vocabulary([p.vocabulaire for p in patterns])
                }
                
                # Sauvegarder le style
                if 'learned_styles' not in st.session_state:
                    st.session_state.learned_styles = {}
                
                st.session_state.learned_styles[type_style] = merged_pattern
                
                st.success(f"✅ Style '{type_style}' appris avec succès à partir de {len(patterns)} documents!")
                
                # Afficher un résumé
                with st.expander("Voir le résumé du style appris"):
                    st.json(merged_pattern)
    else:
        if not type_style and (docs_modeles or uploaded_files):
            st.warning("⚠️ Veuillez spécifier un nom de style")

def show_templates_tab():
    """Affiche l'onglet des modèles"""
    st.markdown("### 📚 Bibliothèque de modèles")
    
    # Options pour générer des modèles dynamiques
    st.markdown("#### 🤖 Générer des modèles personnalisés avec l'IA")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        type_modele_generer = st.text_input(
            "Type d'acte pour lequel générer des modèles",
            placeholder="Ex: Plainte avec constitution de partie civile, Mémoire en défense...",
            key="type_modele_generer"
        )
    
    with col2:
        if st.button("🎯 Générer", key="generer_modeles_button"):
            if type_modele_generer:
                with st.spinner("🤖 Génération de modèles intelligents..."):
                    # Contexte optionnel
                    context = {
                        'client': st.session_state.get('client_nom_acte', ''),
                        'infraction': st.session_state.get('infraction_acte', ''),
                        'juridiction': st.session_state.get('juridiction', '')
                    }
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    modeles = loop.run_until_complete(
                        generate_dynamic_templates(type_modele_generer, context)
                    )
                    
                    # Stocker dans le cache
                    cache_key = f"templates_{clean_key(type_modele_generer)}"
                    st.session_state.dynamic_templates[cache_key] = modeles
                    
                    st.success("✅ Modèles générés avec succès!")
    
    # Afficher les modèles générés dynamiquement
    if st.session_state.dynamic_templates:
        st.markdown("#### 🎨 Modèles générés par IA")
        
        for cache_key, modeles in st.session_state.dynamic_templates.items():
            type_clean = cache_key.replace("templates_", "").replace("_", " ").title()
            
            with st.expander(f"📁 Modèles pour : {type_clean}"):
                for titre, contenu in modeles.items():
                    st.markdown(f"**{titre}**")
                    
                    st.text_area(
                        "Modèle",
                        value=contenu,
                        height=300,
                        key=f"dyn_template_view_{clean_key(titre)}"
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"📋 Utiliser", key=f"use_dyn_template_{clean_key(titre)}"):
                            st.session_state.template_to_use = contenu
                            st.info("Modèle copié. Retournez à l'onglet Rédaction.")
                    
                    with col2:
                        st.download_button(
                            "💾 Télécharger",
                            contenu,
                            f"{clean_key(titre)}.txt",
                            "text/plain",
                            key=f"download_dyn_template_{clean_key(titre)}"
                        )
                    
                    with col3:
                        if st.button("🗑️ Supprimer", key=f"delete_dyn_template_{clean_key(titre)}"):
                            del st.session_state.dynamic_templates[cache_key]
                            st.rerun()
                    
                    st.markdown("---")
    
    # Option pour importer des modèles
    st.markdown("#### 📤 Importer des modèles depuis SharePoint")
    
    if st.button("🔄 Rechercher des modèles dans SharePoint", key="search_templates_sharepoint"):
        templates_found = []
        
        for doc_id, doc in st.session_state.azure_documents.items():
            doc_title_lower = doc.title.lower()
            
            # Identifier les modèles
            if any(term in doc_title_lower for term in ["modèle", "template", "exemple", "type"]):
                templates_found.append(doc)
        
        if templates_found:
            st.success(f"✅ {len(templates_found)} modèles trouvés")
            
            for template in templates_found[:10]:  # Limiter à 10
                with st.expander(f"📄 {template.title}"):
                    st.text_area(
                        "Aperçu",
                        value=template.content[:1000] + "..." if len(template.content) > 1000 else template.content,
                        height=200,
                        key=f"preview_template_{template.id}"
                    )
                    
                    if st.button(f"📥 Importer comme modèle", key=f"import_template_{template.id}"):
                        # Ajouter aux modèles dynamiques
                        cache_key = f"templates_imported_{clean_key(template.title)}"
                        if cache_key not in st.session_state.dynamic_templates:
                            st.session_state.dynamic_templates[cache_key] = {}
                        
                        st.session_state.dynamic_templates[cache_key][f"📄 {template.title}"] = template.content
                        st.success(f"✅ Modèle '{template.title}' importé")
        else:
            st.info("Aucun modèle trouvé dans SharePoint")