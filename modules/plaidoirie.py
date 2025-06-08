# modules/plaidoirie.py
"""Module de génération et gestion des plaidoiries"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict

from config.app_config import LLMProvider, REDACTION_STYLES
from managers.multi_llm_manager import MultiLLMManager
from models.dataclasses import PlaidoirieResult, Document
from utils.helpers import extract_section, format_duration

def process_plaidoirie_request(query: str, analysis: dict):
    """Traite une demande de génération de plaidoirie"""
    
    st.markdown("### 🎤 Génération de plaidoirie")
    
    # Configuration de la plaidoirie
    config = display_plaidoirie_config_interface(analysis)
    
    if st.button("🚀 Générer la plaidoirie", key="generate_plaidoirie", type="primary"):
        with st.spinner("🎯 Génération de la plaidoirie en cours..."):
            result = generate_plaidoirie(config, analysis)
            
            if result:
                st.session_state.plaidoirie_result = result
                display_plaidoirie_results(result)

def display_plaidoirie_config_interface(analysis: dict) -> dict:
    """Interface de configuration pour la plaidoirie"""
    
    config = {}
    
    # Configuration en colonnes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Type d'audience
        config['audience_type'] = st.selectbox(
            "⚖️ Type d'audience",
            ["correctionnelle", "assises", "civile", "commerciale", "prud'homale", "administrative"],
            format_func=lambda x: {
                "correctionnelle": "Tribunal correctionnel",
                "assises": "Cour d'assises",
                "civile": "Tribunal civil",
                "commerciale": "Tribunal de commerce",
                "prud'homale": "Conseil de prud'hommes",
                "administrative": "Tribunal administratif"
            }.get(x, x.title()),
            key="audience_type_select"
        )
        
        # Position
        config['position'] = st.radio(
            "📍 Position",
            ["defense", "partie_civile", "demandeur", "defendeur"],
            format_func=lambda x: {
                "defense": "🛡️ Défense",
                "partie_civile": "⚖️ Partie civile",
                "demandeur": "📋 Demandeur",
                "defendeur": "🛡️ Défendeur"
            }.get(x, x.title()),
            key="position_select"
        )
    
    with col2:
        # Durée cible
        config['duree'] = st.select_slider(
            "⏱️ Durée cible",
            options=["5 min", "10 min", "15 min", "20 min", "30 min", "45 min", "1h"],
            value="20 min",
            key="duree_select"
        )
        
        # Style oratoire
        config['style'] = st.selectbox(
            "🎭 Style oratoire",
            ["classique", "moderne", "emotionnel", "technique", "percutant"],
            format_func=lambda x: {
                "classique": "Classique - Solennel et structuré",
                "moderne": "Moderne - Direct et accessible",
                "emotionnel": "Émotionnel - Touchant et empathique",
                "technique": "Technique - Précis et factuel",
                "percutant": "Percutant - Dynamique et mémorable"
            }.get(x, x.title()),
            key="style_select"
        )
    
    with col3:
        # Options supplémentaires
        config['avec_replique'] = st.checkbox(
            "💬 Inclure réplique",
            value=True,
            help="Préparer une réplique aux arguments adverses",
            key="avec_replique_check"
        )
        
        config['avec_notes'] = st.checkbox(
            "📝 Inclure notes orales",
            value=True,
            help="Ajouter des indications pour l'oral",
            key="avec_notes_check"
        )
        
        config['client_present'] = st.checkbox(
            "👥 Client présent",
            value=True,
            help="Adapter le discours si le client est présent",
            key="client_present_check"
        )
    
    # Éléments du dossier
    with st.expander("📂 Éléments du dossier", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            config['client_name'] = st.text_input(
                "👤 Nom du client",
                value=analysis.get('client', ''),
                key="client_name_input"
            )
            
            config['adversaire'] = st.text_input(
                "⚔️ Partie adverse",
                value=analysis.get('adversaire', ''),
                key="adversaire_input"
            )
        
        with col2:
            config['juridiction'] = st.text_input(
                "🏛️ Juridiction",
                value=analysis.get('juridiction', 'Tribunal'),
                key="juridiction_input"
            )
            
            config['juge'] = st.text_input(
                "👨‍⚖️ Président/Juge",
                placeholder="M./Mme le/la Président(e)",
                key="juge_input"
            )
    
    # Points clés à développer
    config['points_cles'] = st.text_area(
        "🎯 Points clés à développer",
        placeholder="- Premier point fort\n- Deuxième point fort\n- Point de réfutation",
        height=100,
        key="points_cles_textarea"
    )
    
    # Documents à citer
    available_docs = get_available_documents_for_plaidoirie(analysis)
    if available_docs:
        config['documents_citer'] = st.multiselect(
            "📄 Documents à citer",
            options=[doc['title'] for doc in available_docs],
            default=[doc['title'] for doc in available_docs[:5]],
            key="documents_citer_select"
        )
    
    return config

def generate_plaidoirie(config: dict, analysis: dict) -> Optional[PlaidoirieResult]:
    """Génère une plaidoirie complète"""
    
    llm_manager = MultiLLMManager()
    
    if not llm_manager.clients:
        st.error("❌ Aucune IA disponible")
        return None
    
    # Construire le prompt
    prompt = build_plaidoirie_prompt(config, analysis)
    system_prompt = build_plaidoirie_system_prompt(config)
    
    # Déterminer les tokens selon la durée
    duration_tokens = {
        "5 min": 1500,
        "10 min": 2500,
        "15 min": 3500,
        "20 min": 4500,
        "30 min": 6000,
        "45 min": 8000,
        "1h": 10000
    }
    
    max_tokens = duration_tokens.get(config['duree'], 4500)
    
    # Générer la plaidoirie
    provider = list(llm_manager.clients.keys())[0]
    response = llm_manager.query_single_llm(
        provider,
        prompt,
        system_prompt,
        temperature=0.8,  # Plus créatif pour l'oral
        max_tokens=max_tokens
    )
    
    if response['success']:
        # Analyser la plaidoirie générée
        plaidoirie_content = response['response']
        
        # Extraire les éléments
        key_points = extract_key_points(plaidoirie_content)
        structure = extract_plaidoirie_structure(plaidoirie_content)
        oral_markers = extract_oral_markers(plaidoirie_content)
        
        return PlaidoirieResult(
            content=plaidoirie_content,
            type=config['audience_type'],
            style=config['style'],
            duration_estimate=config['duree'],
            key_points=key_points,
            structure=structure,
            oral_markers=oral_markers,
            metadata={
                'position': config['position'],
                'avec_replique': config.get('avec_replique', False),
                'client_present': config.get('client_present', False),
                'provider': response['provider']
            }
        )
    
    return None

def build_plaidoirie_prompt(config: dict, analysis: dict) -> str:
    """Construit le prompt pour générer la plaidoirie"""
    
    # Adapter selon le type d'audience
    audience_context = {
        "correctionnelle": "audience correctionnelle pour une affaire pénale",
        "assises": "audience de cour d'assises pour crime",
        "civile": "audience civile",
        "commerciale": "audience du tribunal de commerce",
        "prud'homale": "audience prud'homale",
        "administrative": "audience du tribunal administratif"
    }
    
    prompt = f"""Rédige une plaidoirie complète et percutante pour une {audience_context.get(config['audience_type'], 'audience')}.

CONTEXTE:
- Position : {config['position']}
- Client : {config.get('client_name', '[Client]')}
- Partie adverse : {config.get('adversaire', '[Adversaire]')}
- Juridiction : {config.get('juridiction', 'Tribunal')}
- Durée cible : {config['duree']}
- Style : {config['style']}

AFFAIRE:
{analysis.get('subject_matter', '')}

POINTS CLÉS À DÉVELOPPER:
{config.get('points_cles', '')}

EXIGENCES POUR LA PLAIDOIRIE:

1. INTRODUCTION (1-2 min)
   - Salutations appropriées à la juridiction
   - Présentation claire de la position défendue
   - Annonce du plan (si plaidoirie longue)
   - Accroche percutante pour capter l'attention

2. DÉVELOPPEMENT ({config['duree']} principal)
   - Arguments structurés et progressifs
   - Utilisation des pièces du dossier
   - Réfutation des arguments adverses
   - Moments d'émotion calculés selon le style
   - Transitions fluides entre les parties

3. PÉRORAISON (1-2 min)
   - Synthèse percutante des arguments
   - Appel à la justice
   - Formule de conclusion appropriée
"""
    
    # Adaptations selon la position
    if config['position'] == 'defense':
        prompt += """
SPÉCIFICITÉS DÉFENSE:
- Insister sur la présomption d'innocence
- Démontrer les failles de l'accusation
- Humaniser le client
- Créer le doute raisonnable
"""
    elif config['position'] == 'partie_civile':
        prompt += """
SPÉCIFICITÉS PARTIE CIVILE:
- Exposer les souffrances subies
- Démontrer le lien de causalité
- Chiffrer les préjudices
- Demander réparation intégrale
"""
    
    # Style oratoire
    style_instructions = {
        "classique": "Style solennel et révérencieux, formules consacrées, structure rigoureuse",
        "moderne": "Style direct et accessible, langage clair, exemples concrets",
        "emotionnel": "Jouer sur les émotions, créer l'empathie, témoignages poignants",
        "technique": "Arguments juridiques précis, citations exactes, rigueur démonstrative",
        "percutant": "Formules choc, rythme soutenu, images marquantes"
    }
    
    prompt += f"\nSTYLE ORATOIRE: {style_instructions.get(config['style'], '')}\n"
    
    # Options spéciales
    if config.get('avec_notes'):
        prompt += """
NOTES POUR L'ORAL:
- Indiquer les pauses avec [pause]
- Marquer les emphases avec [insister]
- Noter les gestes avec [geste: description]
- Indiquer les changements de ton avec [ton: description]
- Marquer les moments de silence avec [silence]
"""
    
    if config.get('avec_replique'):
        prompt += """
INCLURE UNE SECTION RÉPLIQUE:
- Anticiper les arguments adverses principaux
- Préparer des réponses percutantes
- Format: "Si l'on nous objecte que... nous répondrons que..."
"""
    
    if config.get('client_present'):
        prompt += """
ADAPTATION CLIENT PRÉSENT:
- S'adresser parfois directement au client
- Éviter les termes trop techniques
- Valoriser la personne du client
- Montrer l'engagement de la défense
"""
    
    prompt += "\nLa plaidoirie doit être immédiatement utilisable à l'oral, avec un rythme adapté à la durée cible."
    
    return prompt

def build_plaidoirie_system_prompt(config: dict) -> str:
    """Construit le prompt système pour la plaidoirie"""
    
    base_prompt = "Tu es un avocat brillant et charismatique, expert en art oratoire judiciaire."
    
    # Spécialisation selon le type
    specializations = {
        "correctionnelle": "Tu maîtrises parfaitement les plaidoiries pénales devant le tribunal correctionnel.",
        "assises": "Tu excelles dans les grandes plaidoiries d'assises, sachant toucher les jurés.",
        "civile": "Tu es spécialisé dans l'argumentation civile claire et convaincante.",
        "commerciale": "Tu comprends les enjeux commerciaux et sais parler aux juges consulaires.",
        "prud'homale": "Tu maîtrises les spécificités du droit du travail et l'art de convaincre les conseillers.",
        "administrative": "Tu excelles dans l'argumentation technique du contentieux administratif."
    }
    
    base_prompt += f" {specializations.get(config['audience_type'], '')}"
    
    # Style
    style_traits = {
        "classique": "Tu adoptes un style oratoire classique et solennel, digne des grands ténors du barreau.",
        "moderne": "Tu utilises un style moderne et direct, accessible tout en restant professionnel.",
        "emotionnel": "Tu sais manier l'émotion avec finesse pour toucher ton auditoire.",
        "technique": "Tu privilégies la rigueur technique et la précision juridique.",
        "percutant": "Tu as un style percutant et mémorable, avec des formules qui marquent."
    }
    
    base_prompt += f" {style_traits.get(config['style'], '')}"
    
    base_prompt += " Tu structures tes plaidoiries pour maximiser l'impact sur l'auditoire."
    
    return base_prompt

def get_available_documents_for_plaidoirie(analysis: dict) -> List[Dict[str, Any]]:
    """Récupère les documents disponibles pour la plaidoirie"""
    
    documents = []
    
    # Documents de la session
    for doc_id, doc in st.session_state.get('azure_documents', {}).items():
        doc_type = detect_document_type(doc.title, doc.content)
        
        # Prioriser certains types pour la plaidoirie
        if doc_type in ['temoignage', 'expertise', 'procedure']:
            documents.append({
                'id': doc_id,
                'title': doc.title,
                'type': doc_type,
                'relevance': 0.9
            })
        else:
            documents.append({
                'id': doc_id,
                'title': doc.title,
                'type': doc_type,
                'relevance': 0.5
            })
    
    # Trier par pertinence
    documents.sort(key=lambda x: x['relevance'], reverse=True)
    
    return documents[:20]  # Limiter à 20 documents

def detect_document_type(title: str, content: str) -> str:
    """Détecte le type d'un document pour la plaidoirie"""
    title_lower = title.lower()
    content_preview = content[:1000].lower()
    
    if any(kw in title_lower for kw in ['audition', 'interrogatoire', 'garde à vue']):
        return 'temoignage'
    elif any(kw in title_lower for kw in ['expertise', 'expert', 'rapport']):
        return 'expertise'
    elif any(kw in title_lower for kw in ['pv', 'procès-verbal', 'constat']):
        return 'procedure'
    else:
        return 'piece'

def extract_key_points(plaidoirie: str) -> List[str]:
    """Extrait les points clés de la plaidoirie"""
    key_points = []
    
    # Chercher les sections principales
    sections = re.split(r'\n(?=[IVX]+\.|\d+\.)', plaidoirie)
    
    for section in sections:
        # Extraire la première phrase substantielle de chaque section
        lines = section.strip().split('\n')
        for line in lines:
            if len(line) > 50 and not re.match(r'^[IVX]+\.|^\d+\.', line):
                # Nettoyer les marqueurs oraux
                clean_line = re.sub(r'\[.*?\]', '', line).strip()
                if clean_line:
                    key_points.append(clean_line)
                break
    
    # Chercher aussi les phrases avec emphase
    emphases = re.findall(r'\[insister\](.*?)(?:\[|$)', plaidoirie)
    key_points.extend(emphases)
    
    # Dédupliquer et limiter
    seen = set()
    unique_points = []
    for point in key_points:
        if point not in seen and len(point) > 20:
            seen.add(point)
            unique_points.append(point)
    
    return unique_points[:10]

def extract_plaidoirie_structure(content: str) -> Dict[str, List[str]]:
    """Extrait la structure hiérarchique de la plaidoirie"""
    structure = defaultdict(list)
    
    # Diviser en sections principales
    current_section = "Introduction"
    
    lines = content.split('\n')
    
    for line in lines:
        # Détecter les sections principales
        if re.match(r'^[IVX]+\.\s+', line):
            current_section = line.strip()
        # Détecter les sous-sections
        elif re.match(r'^[A-Z]\.\s+', line):
            structure[current_section].append(line.strip())
        # Détecter les marqueurs spéciaux
        elif any(marker in line for marker in ['RÉPLIQUE', 'PÉRORAISON', 'CONCLUSION']):
            current_section = line.strip()
    
    return dict(structure)

def extract_oral_markers(plaidoirie: str) -> List[str]:
    """Extrait les marqueurs pour l'oral"""
    markers = []
    
    # Tous les marqueurs entre crochets
    all_markers = re.findall(r'\[(.*?)\]', plaidoirie)
    
    # Catégoriser
    for marker in all_markers:
        if marker not in markers:
            markers.append(marker)
    
    return markers

def display_plaidoirie_results(result: PlaidoirieResult):
    """Affiche les résultats de la plaidoirie"""
    
    st.success("✅ Plaidoirie générée avec succès!")
    
    # Métadonnées
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Type", result.type.title())
    
    with col2:
        st.metric("Durée estimée", result.duration_estimate)
    
    with col3:
        st.metric("Style", result.style.title())
    
    with col4:
        speaking_time = result.get_speaking_time()
        st.metric("Temps de parole", f"{speaking_time} min")
    
    # Options d'affichage
    view_mode = st.radio(
        "Mode d'affichage",
        ["📄 Texte complet", "🎯 Points clés", "📊 Structure", "🎬 Mode répétition"],
        horizontal=True,
        key="plaidoirie_view_mode"
    )
    
    if view_mode == "📄 Texte complet":
        # Affichage avec mise en forme
        display_plaidoirie_text(result.content)
        
    elif view_mode == "🎯 Points clés":
        st.markdown("### 🎯 Points clés de la plaidoirie")
        for i, point in enumerate(result.key_points, 1):
            st.write(f"**{i}.** {point}")
    
    elif view_mode == "📊 Structure":
        st.markdown("### 📊 Structure de la plaidoirie")
        for section, subsections in result.structure.items():
            with st.expander(section, expanded=True):
                if subsections:
                    for subsection in subsections:
                        st.write(f"• {subsection}")
                else:
                    st.info("Section sans sous-parties")
    
    else:  # Mode répétition
        show_rehearsal_mode(result.content)
    
    # Actions
    st.markdown("### 💾 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Exporter PDF", key="export_plaidoirie_pdf"):
            pdf_content = export_plaidoirie_to_pdf(result)
            st.download_button(
                "💾 Télécharger PDF",
                pdf_content,
                f"plaidoirie_{result.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "application/pdf",
                key="download_plaidoirie_pdf"
            )
    
    with col2:
        if st.button("🎤 Version orateur", key="create_speaker_version"):
            speaker_version = create_speaker_version(result)
            st.download_button(
                "💾 Notes orateur",
                speaker_version.encode('utf-8'),
                f"notes_plaidoirie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain",
                key="download_speaker_notes"
            )
    
    with col3:
        if st.button("📊 Statistiques", key="plaidoirie_stats"):
            show_plaidoirie_statistics(result.content)
    
    with col4:
        if st.button("🗺️ Carte mentale", key="plaidoirie_mindmap"):
            create_plaidoirie_mindmap(result.content)

def display_plaidoirie_text(content: str):
    """Affiche le texte de la plaidoirie avec mise en forme"""
    
    # Remplacer les marqueurs par des émojis/formatting
    formatted_content = content
    
    # Marqueurs de pause
    formatted_content = re.sub(r'\[pause\]', '⏸️', formatted_content)
    formatted_content = re.sub(r'\[silence\]', '🤫', formatted_content)
    
    # Marqueurs d'emphase
    formatted_content = re.sub(r'\[insister\](.*?)(?=\[|$)', r'**\1**', formatted_content)
    
    # Marqueurs de ton
    formatted_content = re.sub(r'\[ton:\s*(.*?)\]', r'🎭 *(\1)*', formatted_content)
    
    # Marqueurs de geste
    formatted_content = re.sub(r'\[geste:\s*(.*?)\]', r'👐 *(\1)*', formatted_content)
    
    # Afficher avec coloration syntaxique basique
    lines = formatted_content.split('\n')
    
    for line in lines:
        if re.match(r'^[IVX]+\.', line):
            st.markdown(f"## {line}")
        elif re.match(r'^[A-Z]\.', line):
            st.markdown(f"### {line}")
        elif line.strip().isupper() and len(line.strip()) > 5:
            st.markdown(f"### {line}")
        else:
            st.write(line)

def show_rehearsal_mode(content: str):
    """Mode répétition pour la plaidoirie"""
    st.markdown("### 🎬 Mode répétition")
    
    # Diviser en sections
    sections = re.split(r'\n\n+', content)
    
    # Navigation entre sections
    if 'rehearsal_section' not in st.session_state:
        st.session_state.rehearsal_section = 0
    
    current_section = st.session_state.rehearsal_section
    
    # Afficher la section courante
    st.info(f"Section {current_section + 1} / {len(sections)}")
    
    st.text_area(
        "Section actuelle",
        value=sections[current_section] if current_section < len(sections) else "",
        height=300,
        key="rehearsal_display"
    )
    
    # Navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Précédent", disabled=current_section == 0):
            st.session_state.rehearsal_section -= 1
            st.rerun()
    
    with col2:
        progress = (current_section + 1) / len(sections)
        st.progress(progress)
        st.write(f"Progression : {progress * 100:.0f}%")
    
    with col3:
        if st.button("Suivant ➡️", disabled=current_section >= len(sections) - 1):
            st.session_state.rehearsal_section += 1
            st.rerun()
    
    # Timer
    with st.expander("⏱️ Chronomètre", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Démarrer", key="start_timer"):
                st.session_state.timer_start = datetime.now()
        
        with col2:
            if st.button("⏸️ Pause", key="pause_timer"):
                if 'timer_start' in st.session_state:
                    elapsed = datetime.now() - st.session_state.timer_start
                    st.write(f"Temps écoulé : {elapsed.seconds // 60}:{elapsed.seconds % 60:02d}")
        
        with col3:
            if st.button("🔄 Réinitialiser", key="reset_timer"):
                if 'timer_start' in st.session_state:
                    del st.session_state.timer_start
    
    # Conseils
    st.markdown("""
    **💡 Conseils répétition :**
    - Répétez debout, comme en audience
    - Enregistrez-vous pour écouter le rythme
    - Marquez physiquement les [pauses]
    - Variez le ton selon les [ton: indications]
    - Pratiquez les gestes indiqués [geste: description]
    - Chronométrez chaque section
    """)

def create_speaker_version(result: PlaidoirieResult) -> str:
    """Crée une version annotée pour l'orateur"""
    
    speaker_notes = f"""NOTES POUR L'ORATEUR
{'=' * 50}

Type d'audience : {result.type}
Durée cible : {result.duration_estimate}
Style : {result.style}

POINTS CLÉS À RETENIR :
{'-' * 30}
"""
    
    for i, point in enumerate(result.key_points, 1):
        speaker_notes += f"{i}. {point}\n"
    
    speaker_notes += f"\n\nTEXTE ANNOTÉ :\n{'=' * 50}\n\n"
    
    # Ajouter des annotations supplémentaires
    annotated_text = result.content
    
    # Marquer les transitions importantes
    annotated_text = re.sub(
        r'(Premièrement|Deuxièmement|Enfin|En conclusion)',
        r'[TRANSITION IMPORTANTE] \1',
        annotated_text
    )
    
    # Marquer les moments clés
    annotated_text = re.sub(
        r'(Il est constant que|Force est de constater|Par conséquent)',
        r'[MOMENT CLÉ] \1',
        annotated_text
    )
    
    speaker_notes += annotated_text
    
    return speaker_notes

def export_plaidoirie_to_pdf(result: PlaidoirieResult) -> bytes:
    """Exporte la plaidoirie en PDF (version simplifiée)"""
    
    # Pour un vrai PDF, utiliser reportlab ou weasyprint
    # Ici version texte formatée
    
    content = f"""PLAIDOIRIE
{result.type.upper()}

Durée estimée : {result.duration_estimate}
Style : {result.style}

{'=' * 50}

{result.content}

{'=' * 50}

POINTS CLÉS :
"""
    
    for i, point in enumerate(result.key_points, 1):
        content += f"\n{i}. {point}"
    
    return content.encode('utf-8')

def show_plaidoirie_statistics(content: str):
    """Affiche les statistiques de la plaidoirie"""
    st.markdown("### 📊 Statistiques de la plaidoirie")
    
    # Calculs
    clean_content = re.sub(r'\[.*?\]', '', content)
    words = clean_content.split()
    sentences = clean_content.split('.')
    
    # Sections
    sections = re.findall(r'^[IVX]+\.\s+.*', content, re.MULTILINE)
    subsections = re.findall(r'^[A-Z]\.\s+.*', content, re.MULTILINE)
    
    # Affichage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mots totaux", f"{len(words):,}")
        st.metric("Phrases", len(sentences))
        st.metric("Mots/minute", f"{len(words) / 150:.0f} min")
    
    with col2:
        st.metric("Sections principales", len(sections))
        st.metric("Sous-sections", len(subsections))
        st.metric("Longueur moyenne phrase", f"{len(words) / max(len(sentences), 1):.1f} mots")
    
    with col3:
        annotations = len(re.findall(r'\[.*?\]', content))
        st.metric("Annotations orales", annotations)
        st.metric("Questions rhétoriques", content.count('?'))
        st.metric("Points d'exclamation", content.count('!'))
    
    # Graphique de répartition
    if sections:
        st.markdown("### 📈 Répartition du contenu")
        section_lengths = []
        
        for i, section in enumerate(sections):
            # Calculer la longueur approximative de chaque section
            start = content.find(section)
            if i < len(sections) - 1:
                end = content.find(sections[i + 1])
            else:
                end = len(content)
            
            section_content = content[start:end]
            section_words = len(section_content.split())
            section_lengths.append({
                'section': section[:50] + '...' if len(section) > 50 else section,
                'words': section_words,
                'percentage': (section_words / len(words)) * 100
            })
        
        # Afficher
        for item in section_lengths:
            st.write(f"**{item['section']}**")
            st.progress(item['percentage'] / 100)
            st.caption(f"{item['words']} mots ({item['percentage']:.1f}%)")

def create_plaidoirie_mindmap(content: str):
    """Crée une carte mentale de la plaidoirie"""
    st.markdown("### 🗺️ Structure en carte mentale")
    
    # Extraire la structure
    structure = extract_plaidoirie_structure(content)
    
    # Afficher sous forme textuelle
    mindmap_text = "PLAIDOIRIE\n"
    
    for section, subsections in structure.items():
        mindmap_text += f"├── {section}\n"
        for i, subsection in enumerate(subsections):
            is_last = i == len(subsections) - 1
            mindmap_text += f"│   {'└' if is_last else '├'}── {subsection[:50]}...\n"
        if subsections:
            mindmap_text += "│\n"
    
    st.code(mindmap_text, language=None)
    
    # Export
    st.download_button(
        "💾 Télécharger structure",
        mindmap_text.encode('utf-8'),
        "structure_plaidoirie.txt",
        "text/plain",
        key="download_mindmap"
    )