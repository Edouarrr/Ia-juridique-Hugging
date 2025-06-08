# modules/email.py
"""Module de gestion des emails pour l'application juridique"""

import streamlit as st
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional
import re

from models.dataclasses import EmailConfig
from utils.helpers import is_valid_email, format_file_size

# Types MIME pour les pièces jointes
ATTACHMENT_MIME_TYPES = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt': 'text/plain',
    'html': 'text/html',
    'json': 'application/json',
    'csv': 'text/csv',
    'zip': 'application/zip'
}

def process_email_request(query: str, analysis: dict):
    """Traite une demande d'envoi par email"""
    
    st.markdown("### 📧 Envoi par email")
    
    # Déterminer les destinataires
    recipients = extract_email_recipients(query, analysis)
    
    # Configuration de l'email
    email_config = create_email_config(recipients, analysis)
    
    # Interface de configuration
    show_email_configuration(email_config)
    
    # Préparer le contenu et les pièces jointes
    prepare_email_content_and_attachments(email_config, analysis)
    
    # Aperçu
    show_email_preview(email_config)
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Envoyer", type="primary", key="send_email_main"):
            send_email_with_progress(email_config)
    
    with col2:
        if st.button("💾 Sauvegarder brouillon", key="save_draft"):
            save_email_draft(email_config)
    
    with col3:
        if st.button("📝 Modifier", key="edit_email"):
            st.session_state.edit_email_mode = True

def extract_email_recipients(query: str, analysis: dict) -> List[str]:
    """Extrait les destinataires depuis la requête"""
    
    recipients = []
    
    # Extraction des emails depuis la requête
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    found_emails = re.findall(email_pattern, query)
    recipients.extend(found_emails)
    
    # Extraction depuis l'analyse
    if analysis.get('entities', {}).get('emails'):
        recipients.extend(analysis['entities']['emails'])
    
    # Récupérer depuis l'historique si pas de destinataires
    if not recipients and st.session_state.get('last_email_recipients'):
        recipients = st.session_state.last_email_recipients
    
    return list(set(recipients))  # Dédupliquer

def create_email_config(recipients: List[str], analysis: dict) -> EmailConfig:
    """Crée la configuration de l'email"""
    
    # Déterminer l'objet selon le contexte
    subject = determine_email_subject(analysis)
    
    # Corps initial
    body = generate_email_body(analysis)
    
    config = EmailConfig(
        to=recipients,
        subject=subject,
        body=body,
        cc=[],
        bcc=[],
        attachments=[],
        priority="normal"
    )
    
    return config

def determine_email_subject(analysis: dict) -> str:
    """Détermine l'objet de l'email selon le contexte"""
    
    if st.session_state.get('redaction_result'):
        doc_type = st.session_state.redaction_result.get('type', 'document')
        reference = analysis.get('reference', '')
        
        subjects = {
            'conclusions': f"Conclusions en défense - {reference}",
            'plainte': f"Dépôt de plainte - {reference}",
            'constitution_pc': f"Constitution de partie civile - {reference}",
            'assignation': f"Assignation - {reference}",
            'mémoire': f"Mémoire - {reference}",
            'courrier': f"Courrier juridique - {reference}"
        }
        
        return subjects.get(doc_type, f"Document juridique - {reference}")
    
    elif st.session_state.get('current_bordereau'):
        return f"Bordereau de communication de pièces - {analysis.get('reference', 'Dossier')}"
    
    elif st.session_state.get('synthesis_result'):
        return f"Synthèse - {analysis.get('reference', 'Dossier')}"
    
    else:
        return f"Document - {datetime.now().strftime('%d/%m/%Y')}"

def generate_email_body(analysis: dict) -> str:
    """Génère le corps de l'email selon le contexte"""
    
    reference = analysis.get('reference', 'votre dossier')
    
    if st.session_state.get('redaction_result'):
        result = st.session_state.redaction_result
        doc_type_names = {
            'conclusions': 'les conclusions en défense',
            'plainte': 'la plainte',
            'constitution_pc': 'la constitution de partie civile',
            'assignation': "l'assignation",
            'mémoire': 'le mémoire',
            'courrier': 'le courrier'
        }
        
        doc_name = doc_type_names.get(result['type'], 'le document')
        
        body = f"""Maître,

Je vous prie de bien vouloir trouver ci-joint {doc_name} concernant {reference}.

Ce document a été préparé conformément à vos instructions et intègre l'ensemble des éléments discutés.

Je reste à votre disposition pour tout complément d'information.

Bien cordialement,

[Votre nom]
[Votre fonction]
[Vos coordonnées]"""

    elif st.session_state.get('current_bordereau'):
        bordereau = st.session_state.current_bordereau
        piece_count = bordereau['metadata']['piece_count']
        
        body = f"""Maître,

Veuillez trouver ci-joint le bordereau de communication de pièces pour {reference}.

Ce bordereau récapitule {piece_count} pièces communiquées, organisées par catégorie.

Les pièces physiques vous seront transmises selon les modalités convenues.

Cordialement,

[Votre nom]"""

    else:
        body = f"""Bonjour,

Veuillez trouver ci-joint le document demandé concernant {reference}.

N'hésitez pas à me contacter pour toute question.

Cordialement,

[Votre nom]"""
    
    return body

def show_email_configuration(email_config: EmailConfig):
    """Interface de configuration de l'email"""
    
    st.markdown("#### 📮 Configuration de l'email")
    
    # Destinataires
    col1, col2, col3 = st.columns(3)
    
    with col1:
        to_addresses = st.text_area(
            "À (To) *",
            value=", ".join(email_config.to),
            help="Séparez les adresses par des virgules",
            key="email_to_field"
        )
        email_config.to = [email.strip() for email in to_addresses.split(',') if email.strip()]
    
    with col2:
        cc_addresses = st.text_area(
            "Cc",
            value=", ".join(email_config.cc),
            help="Copie carbone",
            key="email_cc_field"
        )
        email_config.cc = [email.strip() for email in cc_addresses.split(',') if email.strip()]
    
    with col3:
        bcc_addresses = st.text_area(
            "Cci",
            value=", ".join(email_config.bcc),
            help="Copie carbone invisible",
            key="email_bcc_field"
        )
        email_config.bcc = [email.strip() for email in bcc_addresses.split(',') if email.strip()]
    
    # Validation des emails
    all_emails = email_config.to + email_config.cc + email_config.bcc
    invalid_emails = [email for email in all_emails if not is_valid_email(email)]
    
    if invalid_emails:
        st.error(f"❌ Emails invalides : {', '.join(invalid_emails)}")
    
    # Objet
    email_config.subject = st.text_input(
        "Objet *",
        value=email_config.subject,
        key="email_subject_field"
    )
    
    # Options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        email_config.priority = st.selectbox(
            "Priorité",
            ["low", "normal", "high"],
            index=1,
            format_func=lambda x: {"low": "Faible", "normal": "Normale", "high": "Haute"}[x],
            key="email_priority"
        )
    
    with col2:
        request_receipt = st.checkbox(
            "Accusé de réception",
            key="email_receipt"
        )
    
    with col3:
        request_read = st.checkbox(
            "Confirmation de lecture",
            key="email_read_confirm"
        )

def prepare_email_content_and_attachments(email_config: EmailConfig, analysis: dict):
    """Prépare le contenu et les pièces jointes"""
    
    st.markdown("#### 📎 Pièces jointes")
    
    # Déterminer les pièces jointes potentielles
    available_attachments = get_available_attachments()
    
    if available_attachments:
        selected_attachments = st.multiselect(
            "Sélectionner les pièces jointes",
            options=list(available_attachments.keys()),
            default=list(available_attachments.keys())[:1],  # Premier par défaut
            key="email_attachments_select"
        )
        
        # Format des pièces jointes
        if selected_attachments:
            attachment_format = st.selectbox(
                "Format des documents",
                ["pdf", "docx", "txt"],
                key="attachment_format"
            )
            
            # Préparer les pièces jointes
            for attachment_name in selected_attachments:
                attachment_data = prepare_attachment(
                    attachment_name,
                    available_attachments[attachment_name],
                    attachment_format
                )
                
                if attachment_data:
                    email_config.add_attachment(
                        f"{attachment_name}.{attachment_format}",
                        attachment_data,
                        ATTACHMENT_MIME_TYPES.get(attachment_format, "application/octet-stream")
                    )
        
        # Afficher la liste des pièces jointes
        if email_config.attachments:
            st.info(f"📎 {len(email_config.attachments)} pièce(s) jointe(s)")
            
            for att in email_config.attachments:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"• {att['filename']}")
                
                with col2:
                    st.caption(format_file_size(len(att['data'])))
                
                with col3:
                    if st.button("❌", key=f"remove_att_{att['filename']}"):
                        email_config.attachments.remove(att)
                        st.rerun()
    
    # Upload manuel
    uploaded_files = st.file_uploader(
        "Ajouter d'autres fichiers",
        accept_multiple_files=True,
        key="email_manual_attachments"
    )
    
    if uploaded_files:
        for file in uploaded_files:
            email_config.add_attachment(
                file.name,
                file.read(),
                file.type or "application/octet-stream"
            )

def get_available_attachments() -> Dict[str, Any]:
    """Récupère les documents disponibles pour attachement"""
    
    attachments = {}
    
    # Document rédigé
    if st.session_state.get('redaction_result'):
        result = st.session_state.redaction_result
        attachments[f"{result['type']}_principal"] = {
            'type': 'redaction',
            'content': result['document']
        }
    
    # Bordereau
    if st.session_state.get('current_bordereau'):
        attachments['bordereau_pieces'] = {
            'type': 'bordereau',
            'content': st.session_state.current_bordereau
        }
    
    # Synthèse
    if st.session_state.get('synthesis_result'):
        attachments['synthese'] = {
            'type': 'synthesis',
            'content': st.session_state.synthesis_result.get('content', '')
        }
    
    # Analyse
    if st.session_state.get('ai_analysis_results'):
        attachments['analyse'] = {
            'type': 'analysis',
            'content': st.session_state.ai_analysis_results.get('content', '')
        }
    
    return attachments

def prepare_attachment(name: str, data: Dict[str, Any], format: str) -> bytes:
    """Prépare une pièce jointe dans le format demandé"""
    
    content = data.get('content', '')
    
    if format == 'pdf':
        # Nécessiterait reportlab
        return create_pdf_attachment(content, data['type'])
    
    elif format == 'docx':
        return create_docx_attachment(content, data['type'])
    
    else:  # txt
        return content.encode('utf-8') if isinstance(content, str) else str(content).encode('utf-8')

def create_pdf_attachment(content: Any, doc_type: str) -> bytes:
    """Crée une pièce jointe PDF (placeholder)"""
    # Pour l'instant, retourner le texte
    if isinstance(content, str):
        return content.encode('utf-8')
    elif isinstance(content, dict):
        import json
        return json.dumps(content, indent=2, ensure_ascii=False).encode('utf-8')
    else:
        return str(content).encode('utf-8')

def create_docx_attachment(content: Any, doc_type: str) -> bytes:
    """Crée une pièce jointe DOCX"""
    try:
        import docx
        from docx.shared import Pt
        import io
        
        doc = docx.Document()
        
        # Titre
        doc.add_heading(doc_type.title(), 0)
        
        # Contenu
        if isinstance(content, str):
            # Ajouter le contenu ligne par ligne
            for line in content.split('\n'):
                if line.strip():
                    doc.add_paragraph(line)
        
        elif isinstance(content, dict):
            # Bordereau ou autre structure
            if 'header' in content:
                doc.add_paragraph(content['header'])
            
            if 'pieces' in content:
                doc.add_heading('Pièces', 1)
                for piece in content['pieces']:
                    doc.add_paragraph(f"{piece.numero}. {piece.titre}")
        
        # Sauvegarder
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer.getvalue()
        
    except ImportError:
        # Fallback texte
        return str(content).encode('utf-8')

def show_email_preview(email_config: EmailConfig):
    """Affiche un aperçu de l'email"""
    
    with st.expander("👁️ Aperçu de l'email", expanded=True):
        # En-têtes
        st.markdown("**En-têtes**")
        st.text(f"De : {st.secrets.get('smtp_username', '[Votre email]')}")
        st.text(f"À : {', '.join(email_config.to)}")
        
        if email_config.cc:
            st.text(f"Cc : {', '.join(email_config.cc)}")
        
        if email_config.bcc:
            st.text(f"Cci : {', '.join(email_config.bcc)}")
        
        st.text(f"Objet : {email_config.subject}")
        
        if email_config.priority != "normal":
            st.text(f"Priorité : {email_config.priority}")
        
        st.divider()
        
        # Corps
        st.markdown("**Message**")
        
        # Mode édition ou aperçu
        if st.session_state.get('edit_email_mode'):
            email_config.body = st.text_area(
                "Corps du message",
                value=email_config.body,
                height=300,
                key="edit_email_body"
            )
            
            if st.button("✅ Valider les modifications", key="save_email_edits"):
                st.session_state.edit_email_mode = False
                st.rerun()
        else:
            st.text_area(
                "Corps du message",
                value=email_config.body,
                height=300,
                disabled=True,
                key="preview_email_body"
            )
        
        # Pièces jointes
        if email_config.attachments:
            st.divider()
            st.markdown(f"**Pièces jointes ({len(email_config.attachments)})**")
            
            total_size = sum(len(att['data']) for att in email_config.attachments)
            
            for att in email_config.attachments:
                st.write(f"📎 {att['filename']} ({format_file_size(len(att['data']))})")
            
            st.caption(f"Taille totale : {format_file_size(total_size)}")

def send_email_with_progress(email_config: EmailConfig):
    """Envoie l'email avec barre de progression"""
    
    # Vérifications
    if not email_config.to:
        st.error("❌ Aucun destinataire spécifié")
        return
    
    if not email_config.subject:
        st.error("❌ L'objet est requis")
        return
    
    # Configuration SMTP
    smtp_config = get_smtp_configuration()
    
    if not smtp_config:
        st.error("❌ Configuration email manquante. Configurez les paramètres SMTP.")
        show_smtp_configuration_help()
        return
    
    # Envoi avec progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Étape 1 : Connexion
        status_text.text("📡 Connexion au serveur...")
        progress_bar.progress(20)
        
        msg = create_mime_message(email_config, smtp_config['username'])
        
        # Étape 2 : Authentification
        status_text.text("🔐 Authentification...")
        progress_bar.progress(40)
        
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            
            # Étape 3 : Envoi
            status_text.text("📤 Envoi du message...")
            progress_bar.progress(60)
            
            # Tous les destinataires
            all_recipients = email_config.to + email_config.cc + email_config.bcc
            
            server.send_message(msg, to_addrs=all_recipients)
            
            # Étape 4 : Confirmation
            progress_bar.progress(100)
            status_text.text("✅ Email envoyé avec succès !")
            
            # Sauvegarder l'historique
            save_email_history(email_config)
            
            # Notification de succès
            st.success(f"""
            ✅ Email envoyé avec succès !
            
            **Destinataires :** {len(all_recipients)}
            **Pièces jointes :** {len(email_config.attachments)}
            **Heure d'envoi :** {datetime.now().strftime('%H:%M:%S')}
            """)
            
            # Nettoyer l'état
            st.session_state.last_email_recipients = email_config.to
            
            # Logs
            log_email_sent(email_config)
            
    except smtplib.SMTPAuthenticationError:
        progress_bar.empty()
        status_text.empty()
        st.error("❌ Erreur d'authentification. Vérifiez vos identifiants SMTP.")
        
    except smtplib.SMTPException as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Erreur SMTP : {str(e)}")
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Erreur inattendue : {str(e)}")
        
    finally:
        # Nettoyer l'interface
        import time
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()

def get_smtp_configuration() -> Optional[Dict[str, Any]]:
    """Récupère la configuration SMTP"""
    
    # D'abord vérifier les secrets Streamlit
    if hasattr(st, 'secrets'):
        if all(key in st.secrets for key in ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password']):
            return {
                'server': st.secrets['smtp_server'],
                'port': int(st.secrets['smtp_port']),
                'username': st.secrets['smtp_username'],
                'password': st.secrets['smtp_password']
            }
    
    # Sinon vérifier la configuration en session
    if st.session_state.get('smtp_config'):
        return st.session_state.smtp_config
    
    return None

def create_mime_message(email_config: EmailConfig, from_address: str) -> MIMEMultipart:
    """Crée le message MIME complet"""
    
    msg = MIMEMultipart()
    
    # En-têtes
    msg['From'] = from_address
    msg['To'] = ', '.join(email_config.to)
    
    if email_config.cc:
        msg['Cc'] = ', '.join(email_config.cc)
    
    msg['Subject'] = email_config.subject
    msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    
    # Priorité
    if email_config.priority == "high":
        msg['X-Priority'] = '1'
        msg['Importance'] = 'high'
    elif email_config.priority == "low":
        msg['X-Priority'] = '5'
        msg['Importance'] = 'low'
    
    # Corps du message
    msg.attach(MIMEText(email_config.body, 'plain', 'utf-8'))
    
    # Pièces jointes
    for attachment in email_config.attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment['data'])
        encoders.encode_base64(part)
        
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{attachment["filename"]}"'
        )
        
        msg.attach(part)
    
    return msg

def show_smtp_configuration_help():
    """Affiche l'aide pour la configuration SMTP"""
    
    with st.expander("⚙️ Configuration SMTP requise", expanded=True):
        st.markdown("""
        Pour envoyer des emails, vous devez configurer les paramètres SMTP.
        
        **Option 1 : Via Streamlit Secrets**
        
        Ajoutez dans `.streamlit/secrets.toml` :
        ```toml
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "votre.email@gmail.com"
        smtp_password = "votre_mot_de_passe_app"
        ```
        
        **Option 2 : Configuration manuelle**
        """)
        
        # Formulaire de configuration
        with st.form("smtp_config_form"):
            server = st.text_input("Serveur SMTP", value="smtp.gmail.com")
            port = st.number_input("Port", value=587, min_value=1, max_value=65535)
            username = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            
            if st.form_submit_button("💾 Sauvegarder configuration"):
                st.session_state.smtp_config = {
                    'server': server,
                    'port': port,
                    'username': username,
                    'password': password
                }
                st.success("✅ Configuration sauvegardée pour cette session")
                st.rerun()
        
        st.info("""
        **Note pour Gmail :**
        - Activez la validation en 2 étapes
        - Créez un mot de passe d'application
        - Utilisez ce mot de passe d'application ici
        """)

def save_email_draft(email_config: EmailConfig):
    """Sauvegarde un brouillon d'email"""
    
    if 'email_drafts' not in st.session_state:
        st.session_state.email_drafts = []
    
    draft = {
        'id': f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'created_at': datetime.now(),
        'config': email_config,
        'subject': email_config.subject
    }
    
    st.session_state.email_drafts.append(draft)
    st.success("✅ Brouillon sauvegardé")

def save_email_history(email_config: EmailConfig):
    """Sauvegarde l'historique des emails envoyés"""
    
    if 'email_history' not in st.session_state:
        st.session_state.email_history = []
    
    history_entry = {
        'sent_at': datetime.now(),
        'to': email_config.to,
        'cc': email_config.cc,
        'subject': email_config.subject,
        'attachments_count': len(email_config.attachments),
        'priority': email_config.priority
    }
    
    st.session_state.email_history.append(history_entry)
    
    # Limiter l'historique à 50 entrées
    if len(st.session_state.email_history) > 50:
        st.session_state.email_history = st.session_state.email_history[-50:]

def log_email_sent(email_config: EmailConfig):
    """Enregistre l'envoi dans les logs"""
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': 'email_sent',
        'recipients_count': len(email_config.to + email_config.cc + email_config.bcc),
        'attachments_count': len(email_config.attachments),
        'subject': email_config.subject[:50] + '...' if len(email_config.subject) > 50 else email_config.subject
    }
    
    # Logger (pour le moment, juste print)
    print(f"[EMAIL LOG] {log_entry}")

def show_email_interface():
    """Interface principale de gestion des emails"""
    
    st.markdown("### 📧 Centre de messagerie")
    
    tabs = st.tabs(["📤 Nouveau message", "📝 Brouillons", "📜 Historique", "⚙️ Configuration"])
    
    with tabs[0]:
        # Nouveau message
        process_email_request("", {})
    
    with tabs[1]:
        # Brouillons
        show_email_drafts()
    
    with tabs[2]:
        # Historique
        show_email_history()
    
    with tabs[3]:
        # Configuration
        show_email_configuration_interface()

def show_email_drafts():
    """Affiche les brouillons d'emails"""
    
    drafts = st.session_state.get('email_drafts', [])
    
    if not drafts:
        st.info("Aucun brouillon sauvegardé")
        return
    
    st.write(f"**{len(drafts)} brouillon(s)**")
    
    # Afficher les brouillons du plus récent au plus ancien
    for draft in reversed(drafts):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.write(f"**{draft['subject']}**")
                st.caption(f"Créé le {draft['created_at'].strftime('%d/%m/%Y à %H:%M')}")
            
            with col2:
                recipients = ", ".join(draft['config'].to[:2])
                if len(draft['config'].to) > 2:
                    recipients += f" +{len(draft['config'].to) - 2}"
                st.caption(f"À : {recipients}")
            
            with col3:
                if st.button("📝", key=f"edit_draft_{draft['id']}"):
                    st.session_state.current_email_config = draft['config']
                    st.rerun()
            
            with col4:
                if st.button("🗑️", key=f"delete_draft_{draft['id']}"):
                    st.session_state.email_drafts.remove(draft)
                    st.rerun()
        
        st.divider()

def show_email_history():
    """Affiche l'historique des emails envoyés"""
    
    history = st.session_state.get('email_history', [])
    
    if not history:
        st.info("Aucun email envoyé")
        return
    
    st.write(f"**{len(history)} email(s) envoyé(s)**")
    
    # Filtres
    col1, col2 = st.columns(2)
    
    with col1:
        date_filter = st.date_input(
            "Filtrer par date",
            value=None,
            key="email_history_date_filter"
        )
    
    with col2:
        search_filter = st.text_input(
            "Rechercher dans l'objet",
            key="email_history_search"
        )
    
    # Appliquer les filtres
    filtered_history = history
    
    if date_filter:
        filtered_history = [
            h for h in filtered_history 
            if h['sent_at'].date() == date_filter
        ]
    
    if search_filter:
        filtered_history = [
            h for h in filtered_history 
            if search_filter.lower() in h['subject'].lower()
        ]
    
    # Afficher l'historique filtré
    for entry in reversed(filtered_history[-20:]):  # Derniers 20
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.write(f"**{entry['subject']}**")
                st.caption(f"Envoyé le {entry['sent_at'].strftime('%d/%m/%Y à %H:%M')}")
            
            with col2:
                recipients = ", ".join(entry['to'][:2])
                if len(entry['to']) > 2:
                    recipients += f" +{len(entry['to']) - 2}"
                st.caption(f"À : {recipients}")
                
                if entry['cc']:
                    st.caption(f"Cc : {len(entry['cc'])} destinataire(s)")
            
            with col3:
                if entry['attachments_count'] > 0:
                    st.caption(f"📎 {entry['attachments_count']}")
            
            with col4:
                if entry['priority'] == "high":
                    st.caption("🔴 Haute")
                elif entry['priority'] == "low":
                    st.caption("🔵 Faible")
        
        st.divider()
    
    # Export de l'historique
    if st.button("📥 Exporter l'historique"):
        export_email_history(filtered_history)

def export_email_history(history: List[Dict[str, Any]]):
    """Exporte l'historique des emails"""
    
    import json
    
    export_data = []
    
    for entry in history:
        export_entry = {
            'date': entry['sent_at'].isoformat(),
            'destinataires': ', '.join(entry['to']),
            'cc': ', '.join(entry.get('cc', [])),
            'objet': entry['subject'],
            'pieces_jointes': entry.get('attachments_count', 0),
            'priorite': entry.get('priority', 'normal')
        }
        export_data.append(export_entry)
    
    # JSON
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    st.download_button(
        "💾 Télécharger (JSON)",
        json_str,
        f"historique_emails_{datetime.now().strftime('%Y%m%d')}.json",
        "application/json",
        key="download_email_history"
    )

def show_email_configuration_interface():
    """Interface de configuration des emails"""
    
    st.markdown("#### ⚙️ Configuration email")
    
    # État de la configuration
    smtp_config = get_smtp_configuration()
    
    if smtp_config:
        st.success(f"✅ Configuré ({smtp_config['server']})")
        
        # Test de connexion
        if st.button("🔌 Tester la connexion"):
            test_smtp_connection(smtp_config)
    else:
        st.warning("❌ Non configuré")
        show_smtp_configuration_help()
    
    # Templates d'emails
    st.markdown("#### 📝 Templates d'emails")
    
    email_templates = st.session_state.get('email_templates', get_default_email_templates())
    
    for template_name, template in email_templates.items():
        with st.expander(f"📧 {template['name']}"):
            st.text_area(
                "Objet",
                value=template['subject'],
                key=f"template_subject_{template_name}",
                height=50
            )
            
            st.text_area(
                "Corps",
                value=template['body'],
                key=f"template_body_{template_name}",
                height=200
            )
            
            if st.button(f"💾 Sauvegarder", key=f"save_template_{template_name}"):
                # Sauvegarder les modifications
                template['subject'] = st.session_state[f"template_subject_{template_name}"]
                template['body'] = st.session_state[f"template_body_{template_name}"]
                st.success("✅ Template sauvegardé")
    
    # Signatures
    st.markdown("#### ✍️ Signatures")
    
    signatures = st.session_state.get('email_signatures', get_default_signatures())
    
    selected_signature = st.selectbox(
        "Signature par défaut",
        options=list(signatures.keys()),
        format_func=lambda x: signatures[x]['name'],
        key="default_signature"
    )
    
    for sig_key, signature in signatures.items():
        with st.expander(f"✍️ {signature['name']}"):
            signature['content'] = st.text_area(
                "Contenu",
                value=signature['content'],
                key=f"signature_{sig_key}",
                height=150
            )

def test_smtp_connection(smtp_config: Dict[str, Any]):
    """Teste la connexion SMTP"""
    
    with st.spinner("Test de connexion en cours..."):
        try:
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.quit()
            
            st.success("✅ Connexion réussie !")
            
        except smtplib.SMTPAuthenticationError:
            st.error("❌ Erreur d'authentification")
            
        except smtplib.SMTPException as e:
            st.error(f"❌ Erreur SMTP : {str(e)}")
            
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

def get_default_email_templates() -> Dict[str, Dict[str, str]]:
    """Retourne les templates d'emails par défaut"""
    
    return {
        'document_juridique': {
            'name': 'Document juridique',
            'subject': 'Document juridique - [Référence]',
            'body': """Maître,

Je vous prie de bien vouloir trouver ci-joint le document demandé concernant [référence].

Ce document a été préparé conformément à vos instructions.

Je reste à votre disposition pour tout complément d'information.

Bien cordialement,"""
        },
        'bordereau_pieces': {
            'name': 'Bordereau de pièces',
            'subject': 'Bordereau de communication de pièces - [Référence]',
            'body': """Maître,

Veuillez trouver ci-joint le bordereau de communication de pièces pour [référence].

Les pièces physiques vous seront transmises selon les modalités convenues.

Cordialement,"""
        },
        'transmission_urgente': {
            'name': 'Transmission urgente',
            'subject': 'URGENT - [Objet] - [Référence]',
            'body': """Maître,

Suite à notre échange, je vous transmets en urgence [description].

Compte tenu des délais, je vous serais reconnaissant de bien vouloir me confirmer la bonne réception.

Bien cordialement,"""
        }
    }

def get_default_signatures() -> Dict[str, Dict[str, str]]:
    """Retourne les signatures par défaut"""
    
    return {
        'formelle': {
            'name': 'Formelle',
            'content': """[Votre nom]
[Votre fonction]
[Cabinet/Société]
[Téléphone]
[Email]"""
        },
        'simple': {
            'name': 'Simple',
            'content': """Cordialement,

[Votre nom]
[Téléphone]"""
        },
        'complete': {
            'name': 'Complète',
            'content': """[Votre nom]
[Votre fonction]

[Cabinet/Société]
[Adresse]
[Code postal] [Ville]

Tél : [Téléphone]
Mobile : [Mobile]
Email : [Email]

Ce message et ses pièces jointes sont confidentiels et établis à l'intention exclusive de leur destinataire."""
        }
    }

# Fonction pour intégration avec d'autres modules
def prepare_and_send_document(document_type: str, content: str, reference: str = ""):
    """Prépare et envoie un document par email"""
    
    # Créer la configuration
    email_config = EmailConfig(
        to=[],
        subject=f"{document_type.title()} - {reference}",
        body=generate_email_body({'reference': reference})
    )
    
    # Ajouter le document en pièce jointe
    attachment_data = create_docx_attachment(content, document_type)
    email_config.add_attachment(
        f"{document_type}_{datetime.now().strftime('%Y%m%d')}.docx",
        attachment_data,
        ATTACHMENT_MIME_TYPES['docx']
    )
    
    # Stocker la configuration
    st.session_state.current_email_config = email_config
    
    # Rediriger vers l'interface email
    st.session_state.current_page = 'email'
    st.rerun()