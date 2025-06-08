# modules/redaction_courrier.py
"""Page de rédaction de courrier avec papier en-tête"""

import streamlit as st
import io
import asyncio
from datetime import datetime

from config.app_config import LLMProvider
from models.dataclasses import LetterheadTemplate
from managers.multi_llm_manager import MultiLLMManager
from utils.helpers import clean_key, create_letterhead_from_template

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

def show_page():
    """Affiche la page de rédaction de courrier"""
    st.header("✉️ Rédaction de courrier")
    
    # Vérifier si un papier en-tête est configuré
    if 'letterhead_template' not in st.session_state or st.session_state.letterhead_template is None:
        show_letterhead_setup()
        return
    
    # Afficher le papier en-tête actuel
    with st.expander("📄 Papier en-tête actuel", expanded=False):
        template = st.session_state.letterhead_template
        st.text(template.header_content)
        st.caption(f"Pied de page : {template.footer_content}")
    
    # Formulaire de rédaction
    show_letter_form()

def show_letterhead_setup():
    """Affiche la configuration rapide du papier en-tête"""
    st.warning("⚠️ Aucun papier en-tête configuré. Veuillez d'abord configurer votre papier en-tête.")
    
    if st.button("➕ Créer un papier en-tête rapide"):
        with st.form("quick_letterhead"):
            st.markdown("### Configuration rapide du papier en-tête")
            
            col1, col2 = st.columns(2)
            
            with col1:
                cabinet_nom = st.text_input("Nom du cabinet", placeholder="Cabinet d'avocats...")
                avocat_nom = st.text_input("Nom de l'avocat", placeholder="Maître...")
                barreau = st.text_input("Barreau", placeholder="Barreau de Paris")
            
            with col2:
                adresse = st.text_area("Adresse", placeholder="123 rue de la Justice\n75001 Paris")
                telephone = st.text_input("Téléphone", placeholder="01 23 45 67 89")
                email = st.text_input("Email", placeholder="contact@cabinet.fr")
            
            if st.form_submit_button("Créer le papier en-tête"):
                # Créer l'en-tête
                header_content = f"""{cabinet_nom}
{avocat_nom}
Avocat au {barreau}
{adresse}
Tél : {telephone}
Email : {email}"""
                
                # Créer le pied de page
                footer_content = f"{cabinet_nom} - {adresse} - Tél : {telephone}"
                
                # Créer le template
                st.session_state.letterhead_template = LetterheadTemplate(
                    name="Papier en-tête principal",
                    header_content=header_content,
                    footer_content=footer_content
                )
                
                st.success("✅ Papier en-tête créé avec succès!")
                st.rerun()

def show_letter_form():
    """Affiche le formulaire de rédaction du courrier"""
    st.markdown("### 📝 Nouveau courrier")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Destinataire
        destinataire_nom = st.text_input(
            "Destinataire",
            placeholder="Nom du destinataire",
            key="courrier_destinataire_nom"
        )
        
        destinataire_qualite = st.text_input(
            "Qualité",
            placeholder="Ex: Procureur de la République, Directeur...",
            key="courrier_destinataire_qualite"
        )
        
        destinataire_adresse = st.text_area(
            "Adresse",
            placeholder="Adresse complète du destinataire",
            height=80,
            key="courrier_destinataire_adresse"
        )
    
    with col2:
        # Informations courrier
        objet = st.text_input(
            "Objet",
            placeholder="Objet du courrier",
            key="courrier_objet"
        )
        
        reference = st.text_input(
            "Référence",
            placeholder="Votre référence / Notre référence",
            key="courrier_reference"
        )
        
        date_courrier = st.date_input(
            "Date",
            value=datetime.now(),
            key="courrier_date"
        )
        
        pieces_jointes = st.text_area(
            "Pièces jointes",
            placeholder="Liste des pièces jointes (optionnel)",
            height=60,
            key="courrier_pj"
        )
    
    # Type de courrier
    show_letter_type_selection()
    
    # Contenu principal
    show_letter_content()
    
    # Affichage et export
    if 'courrier_content' in st.session_state and st.session_state.courrier_content:
        show_letter_preview_and_export(destinataire_nom, destinataire_qualite, 
                                      destinataire_adresse, objet, reference, 
                                      date_courrier, pieces_jointes)

def show_letter_type_selection():
    """Affiche la sélection du type de courrier"""
    st.markdown("### 📨 Type de courrier")
    
    st.session_state.type_courrier = st.selectbox(
        "Sélectionner le type",
        [
            "Courrier simple",
            "Demande d'information",
            "Demande d'audition",
            "Transmission de pièces",
            "Réponse à courrier",
            "Mise en demeure",
            "Notification",
            "Autre"
        ],
        key="courrier_type_select"
    )

def show_letter_content():
    """Affiche la section de contenu du courrier"""
    st.markdown("### 📄 Contenu du courrier")
    
    mode_redaction = st.radio(
        "Mode de rédaction",
        ["Rédaction assistée par IA", "Rédaction manuelle"],
        key="courrier_mode"
    )
    
    if mode_redaction == "Rédaction assistée par IA":
        show_ai_assisted_content()
    else:
        show_manual_content()

def show_ai_assisted_content():
    """Affiche le formulaire de rédaction assistée par IA"""
    points_courrier = st.text_area(
        "Points clés à développer",
        placeholder="""Ex:
- Demander un rendez-vous
- Rappeler la procédure en cours
- Solliciter la communication de pièces
- Proposer des dates de disponibilité""",
        height=150,
        key="courrier_points"
    )
    
    # Options de génération
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.ton_courrier = st.select_slider(
            "Ton",
            options=["Très formel", "Formel", "Courtois", "Direct"],
            value="Formel",
            key="courrier_ton"
        )
    
    with col2:
        st.session_state.style_courrier = st.select_slider(
            "Style",
            options=["Concis", "Standard", "Détaillé"],
            value="Standard",
            key="courrier_style"
        )
    
    # Bouton de génération
    if st.button("🤖 Générer le courrier", type="primary", key="generer_courrier_ia"):
        generate_letter_with_ai(points_courrier)

def show_manual_content():
    """Affiche la zone de rédaction manuelle"""
    contenu_manuel = st.text_area(
        "Contenu du courrier",
        placeholder="Rédigez votre courrier ici...",
        height=400,
        key="courrier_contenu_manuel"
    )
    
    if contenu_manuel:
        st.session_state.courrier_content = contenu_manuel

def generate_letter_with_ai(points_courrier):
    """Génère le courrier avec l'IA"""
    if not st.session_state.get('courrier_destinataire_nom') or not st.session_state.get('courrier_objet') or not points_courrier:
        st.error("❌ Veuillez remplir tous les champs obligatoires")
        return
    
    # Construire le prompt
    prompt = f"""Tu es un avocat rédigeant un courrier professionnel.
Type de courrier : {st.session_state.type_courrier}
Destinataire : {st.session_state.courrier_destinataire_nom} ({st.session_state.get('courrier_destinataire_qualite', '')})
Objet : {st.session_state.courrier_objet}
Référence : {st.session_state.get('courrier_reference', 'Aucune')}
Points à développer : {points_courrier}
Ton : {st.session_state.ton_courrier}
Style : {st.session_state.style_courrier}
{"Pièces jointes : " + st.session_state.get('courrier_pj', '') if st.session_state.get('courrier_pj') else ""}
Rédige un courrier professionnel complet avec :
- Une formule d'appel appropriée
- Une introduction claire
- Le développement des points demandés
- Une conclusion adaptée
- Une formule de politesse conforme aux usages
Ne pas inclure l'en-tête ni l'adresse (sera ajouté automatiquement)."""
    
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
                    "Tu es un avocat expert en rédaction de courriers professionnels. Tes courriers sont toujours clairs, courtois et efficaces."
                )
            )
            
            if response['success']:
                st.session_state.courrier_content = response['response']
                st.success("✅ Courrier généré avec succès!")
            else:
                st.error(f"❌ Erreur : {response['error']}")
        else:
            st.error("❌ Aucune IA disponible")

def show_letter_preview_and_export(destinataire_nom, destinataire_qualite, 
                                  destinataire_adresse, objet, reference, 
                                  date_courrier, pieces_jointes):
    """Affiche la prévisualisation et les options d'export"""
    st.markdown("### ✏️ Courrier généré")
    
    # Édition possible
    courrier_final = st.text_area(
        "Vous pouvez modifier le courrier",
        value=st.session_state.courrier_content,
        height=400,
        key="courrier_final_edit"
    )
    
    # Prévisualisation avec papier en-tête
    if st.button("👁️ Prévisualiser avec papier en-tête", key="preview_courrier"):
        show_letter_preview(destinataire_nom, destinataire_qualite,
                          destinataire_adresse, objet, reference,
                          date_courrier, courrier_final)
    
    # Options d'export
    show_export_options(destinataire_nom, destinataire_qualite,
                       destinataire_adresse, objet, reference,
                       date_courrier, courrier_final, pieces_jointes)

def show_letter_preview(destinataire_nom, destinataire_qualite,
                       destinataire_adresse, objet, reference,
                       date_courrier, courrier_final):
    """Affiche la prévisualisation du courrier avec papier en-tête"""
    st.markdown("### 📄 Prévisualisation")
    
    template = st.session_state.letterhead_template
    
    # Construire le courrier complet
    courrier_complet = f"""{template.header_content}
{destinataire_nom}
{destinataire_qualite}
{destinataire_adresse}
{date_courrier.strftime('%d %B %Y')}
Objet : {objet}
{"Réf : " + reference if reference else ""}
{courrier_final}
{template.footer_content}"""
    
    # Afficher dans un conteneur stylé
    st.markdown('<div class="letterhead-preview">', unsafe_allow_html=True)
    st.text(courrier_complet)
    st.markdown('</div>', unsafe_allow_html=True)

def show_export_options(destinataire_nom, destinataire_qualite,
                       destinataire_adresse, objet, reference,
                       date_courrier, courrier_final, pieces_jointes):
    """Affiche les options d'export"""
    st.markdown("### 💾 Export")
    
    template = st.session_state.letterhead_template
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export texte simple
        courrier_complet_export = f"""{template.header_content}
{destinataire_nom}
{destinataire_qualite}
{destinataire_adresse}
{date_courrier.strftime('%d %B %Y')}
Objet : {objet}
{"Réf : " + reference if reference else ""}
{courrier_final}
{template.footer_content}"""
        
        st.download_button(
            "💾 Télécharger (.txt)",
            courrier_complet_export,
            f"courrier_{clean_key(objet)}_{date_courrier.strftime('%Y%m%d')}.txt",
            "text/plain",
            key="download_courrier_txt"
        )
    
    with col2:
        if DOCX_AVAILABLE:
            # Créer le document Word avec papier en-tête
            docx_buffer = create_letterhead_from_template(
                template,
                f"""{destinataire_nom}
{destinataire_qualite}
{destinataire_adresse}
{date_courrier.strftime('%d %B %Y')}
Objet : {objet}
{"Réf : " + reference if reference else ""}
{courrier_final}"""
            )
            
            if docx_buffer:
                st.download_button(
                    "💾 Télécharger (.docx)",
                    docx_buffer.getvalue(),
                    f"courrier_{clean_key(objet)}_{date_courrier.strftime('%Y%m%d')}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_courrier_docx"
                )
    
    with col3:
        if st.button("📧 Préparer l'envoi par email", key="prepare_email"):
            st.info("📧 Copier le contenu ci-dessous dans votre client email")
            st.code(courrier_final)
