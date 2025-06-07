# pages/assistant.py
"""Page d'assistant interactif - Chatbot juridique expert"""

import streamlit as st
import asyncio
from datetime import datetime
import json
from typing import Dict, List, Optional

from config.app_config import TYPES_INFRACTIONS
from managers import LLMManager, display_model_selector, display_model_params
from utils import load_custom_css, create_alert_box, format_date, sanitize_text

def show():
    """Affiche la page d'assistant interactif"""
    load_custom_css()
    
    st.title("💬 Assistant juridique interactif")
    st.markdown("Posez vos questions juridiques et obtenez des réponses d'expert instantanées")
    
    # Initialiser le gestionnaire LLM et l'historique
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = LLMManager()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = generate_session_id()
    
    # Layout en colonnes
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Zone de chat principale
        show_chat_interface()
    
    with col2:
        # Panneau de configuration
        show_config_panel()

def show_chat_interface():
    """Interface de chat principale"""
    # Conteneur pour l'historique des messages
    chat_container = st.container()
    
    with chat_container:
        # Afficher l'historique
        for message in st.session_state.chat_history:
            display_message(message)
    
    # Séparateur
    st.markdown("---")
    
    # Zone de saisie avec colonnes
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_area(
            "Votre question juridique",
            height=100,
            placeholder="""Exemples de questions :
- Quels sont les éléments constitutifs de l'abus de biens sociaux ?
- Quelle est la jurisprudence récente sur la corruption ?
- Comment prouver l'élément intentionnel dans une escroquerie ?
- Quelles sont les sanctions encourues pour du blanchiment ?""",
            key="user_input"
        )
    
    with col2:
        # Boutons d'action empilés
        send_button = st.button(
            "📤 Envoyer",
            type="primary",
            use_container_width=True,
            disabled=not user_input
        )
        
        clear_button = st.button(
            "🗑️ Effacer",
            use_container_width=True
        )
        
        if st.session_state.chat_history:
            export_button = st.button(
                "💾 Exporter",
                use_container_width=True
            )
        else:
            export_button = False
    
    # Actions
    if send_button and user_input:
        handle_user_input(user_input)
    
    if clear_button:
        if st.session_state.chat_history:
            # Sauvegarder la session avant d'effacer
            save_current_session()
        st.session_state.chat_history = []
        st.rerun()
    
    if export_button:
        export_chat_history()
    
    # Suggestions de questions
    show_question_suggestions()

def show_config_panel():
    """Panneau de configuration du chat"""
    st.markdown("### ⚙️ Configuration")
    
    # Sélection du modèle
    with st.expander("Modèle IA", expanded=True):
        provider, model = display_model_selector()
        
        # Bouton pour appliquer
        if st.button("Appliquer", key="apply_model"):
            try:
                st.session_state.llm_manager.set_current_model(provider, model)
                st.success(f"Modèle {provider}/{model} activé")
            except Exception as e:
                st.error(f"Erreur : {str(e)}")
    
    # Paramètres avancés
    with st.expander("Paramètres avancés"):
        params = display_model_params()
        st.session_state['chat_params'] = params
    
    # Mode de réponse
    with st.expander("Mode de réponse"):
        response_mode = st.radio(
            "Style de réponse",
            ["Concis", "Détaillé", "Pédagogique"],
            index=1
        )
        
        include_sources = st.checkbox(
            "Inclure les sources",
            value=True
        )
        
        verify_jurisprudence = st.checkbox(
            "Vérifier les jurisprudences",
            value=True
        )
        
        st.session_state['response_config'] = {
            'mode': response_mode,
            'include_sources': include_sources,
            'verify_jurisprudence': verify_jurisprudence
        }
    
    # Contexte spécialisé
    with st.expander("Contexte"):
        specialization = st.selectbox(
            "Spécialisation",
            ["Général"] + TYPES_INFRACTIONS
        )
        
        expertise_level = st.select_slider(
            "Niveau d'expertise",
            ["Débutant", "Intermédiaire", "Expert"],
            value="Intermédiaire"
        )
        
        st.session_state['context_config'] = {
            'specialization': specialization,
            'expertise_level': expertise_level
        }
    
    # Historique des sessions
    with st.expander("Sessions sauvegardées"):
        show_saved_sessions()

def handle_user_input(user_input: str):
    """Traite l'entrée utilisateur et génère une réponse"""
    # Nettoyer l'entrée
    clean_input = sanitize_text(user_input)
    
    # Ajouter le message utilisateur
    user_message = {
        'role': 'user',
        'content': clean_input,
        'timestamp': datetime.now()
    }
    st.session_state.chat_history.append(user_message)
    
    # Afficher le message utilisateur immédiatement
    display_message(user_message)
    
    # Générer la réponse
    with st.spinner("L'assistant réfléchit..."):
        try:
            # Préparer le contexte
            system_prompt = create_system_prompt()
            
            # Obtenir les paramètres
            params = st.session_state.get('chat_params', {})
            
            # Générer la réponse de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(
                st.session_state.llm_manager.generate_response(
                    clean_input,
                    system_prompt=system_prompt,
                    **params
                )
            )
            
            # Ajouter la réponse à l'historique
            assistant_message = {
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now(),
                'model': f"{st.session_state.llm_manager.current_provider}/{st.session_state.llm_manager.current_model}"
            }
            st.session_state.chat_history.append(assistant_message)
            
            # Afficher la réponse
            display_message(assistant_message)
            
            # Vérifier les jurisprudences si demandé
            if st.session_state.get('response_config', {}).get('verify_jurisprudence'):
                check_jurisprudences_in_response(response)
            
            # Incrémenter le compteur de messages
            st.session_state['messages_count'] = st.session_state.get('messages_count', 0) + 1
            
        except Exception as e:
            st.error(f"Erreur lors de la génération de la réponse : {str(e)}")
            error_message = {
                'role': 'system',
                'content': f"Erreur : {str(e)}",
                'timestamp': datetime.now()
            }
            st.session_state.chat_history.append(error_message)

def display_message(message: Dict):
    """Affiche un message dans le chat"""
    role = message['role']
    content = message['content']
    timestamp = message.get('timestamp', datetime.now())
    
    if role == 'user':
        with st.chat_message("user", avatar="👤"):
            st.markdown(content)
            st.caption(format_date(timestamp, "%H:%M"))
    
    elif role == 'assistant':
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown(content)
            
            # Afficher le modèle utilisé
            if 'model' in message:
                st.caption(f"{format_date(timestamp, '%H:%M')} • {message['model']}")
            else:
                st.caption(format_date(timestamp, "%H:%M"))
    
    elif role == 'system':
        with st.chat_message("system", avatar="ℹ️"):
            st.info(content)
            st.caption(format_date(timestamp, "%H:%M"))

def create_system_prompt() -> str:
    """Crée le prompt système basé sur la configuration"""
    config = st.session_state.get('response_config', {})
    context = st.session_state.get('context_config', {})
    
    base_prompt = """Tu es un expert en droit pénal des affaires français avec 20 ans d'expérience.
Tu fournis des conseils juridiques précis et fiables.
Tu cites toujours les sources légales et jurisprudentielles exactes."""
    
    # Adapter selon le mode
    if config.get('mode') == 'Concis':
        base_prompt += "\nRéponds de manière concise et directe, en allant à l'essentiel."
    elif config.get('mode') == 'Pédagogique':
        base_prompt += "\nExplique de manière pédagogique, avec des exemples concrets."
    else:
        base_prompt += "\nFournis des réponses détaillées et structurées."
    
    # Spécialisation
    if context.get('specialization') != 'Général':
        base_prompt += f"\nTu es spécialisé en {context['specialization']}."
    
    # Niveau d'expertise
    if context.get('expertise_level') == 'Débutant':
        base_prompt += "\nAdapte tes réponses pour un public débutant, évite le jargon complexe."
    elif context.get('expertise_level') == 'Expert':
        base_prompt += "\nUtilise un niveau technique élevé approprié pour des juristes expérimentés."
    
    # Sources
    if config.get('include_sources'):
        base_prompt += "\nCite systématiquement les articles de loi et jurisprudences pertinentes."
    
    return base_prompt

def show_question_suggestions():
    """Affiche des suggestions de questions"""
    st.markdown("### 💡 Suggestions de questions")
    
    suggestions = [
        "Quelle est la différence entre corruption active et passive ?",
        "Comment prouver la mauvaise foi dans l'abus de biens sociaux ?",
        "Quelles sont les obligations de déclaration TRACFIN ?",
        "Quelle est la prescription pour le délit d'initié ?",
        "Comment fonctionne la CJIP (Convention Judiciaire d'Intérêt Public) ?"
    ]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"❓ {suggestion}", key=f"sugg_{i}", use_container_width=True):
                st.session_state.user_input = suggestion
                st.rerun()

def check_jurisprudences_in_response(response: str):
    """Vérifie les jurisprudences mentionnées dans la réponse"""
    if 'jurisprudence_verifier' in st.session_state:
        verifier = st.session_state.jurisprudence_verifier
        references = verifier.extract_references_from_text(response)
        
        if references:
            with st.expander("🔍 Vérification des jurisprudences citées", expanded=False):
                st.info(f"{len(references)} références détectées. Vérification en cours...")
                
                # Ici, on pourrait lancer la vérification async
                # Pour l'instant, on affiche juste les références
                for ref in references:
                    st.caption(f"- {ref.to_citation()}")

def export_chat_history():
    """Exporte l'historique du chat"""
    if not st.session_state.chat_history:
        st.warning("Aucun historique à exporter")
        return
    
    # Préparer les données
    export_data = {
        'session_id': st.session_state.current_session_id,
        'date': datetime.now().isoformat(),
        'messages': []
    }
    
    for msg in st.session_state.chat_history:
        export_data['messages'].append({
            'role': msg['role'],
            'content': msg['content'],
            'timestamp': msg['timestamp'].isoformat() if isinstance(msg['timestamp'], datetime) else msg['timestamp'],
            'model': msg.get('model', 'N/A')
        })
    
    # Créer le fichier
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    # Bouton de téléchargement
    st.download_button(
        label="📥 Télécharger l'historique",
        data=json_str,
        file_name=f"chat_juridique_{st.session_state.current_session_id}.json",
        mime="application/json"
    )

def save_current_session():
    """Sauvegarde la session actuelle"""
    if st.session_state.chat_history:
        session_data = {
            'id': st.session_state.current_session_id,
            'date': datetime.now(),
            'messages': st.session_state.chat_history,
            'message_count': len(st.session_state.chat_history)
        }
        
        st.session_state.chat_sessions[st.session_state.current_session_id] = session_data
        
        # Limiter à 10 sessions sauvegardées
        if len(st.session_state.chat_sessions) > 10:
            oldest_id = min(st.session_state.chat_sessions.keys())
            del st.session_state.chat_sessions[oldest_id]
        
        # Générer un nouvel ID de session
        st.session_state.current_session_id = generate_session_id()

def show_saved_sessions():
    """Affiche les sessions sauvegardées"""
    if not st.session_state.chat_sessions:
        st.info("Aucune session sauvegardée")
        return
    
    for session_id, session_data in st.session_state.chat_sessions.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.caption(f"**{format_date(session_data['date'])}**")
            st.caption(f"{session_data['message_count']} messages")
        
        with col2:
            if st.button("📂", key=f"load_{session_id}", help="Charger"):
                load_session(session_id)

def load_session(session_id: str):
    """Charge une session sauvegardée"""
    if session_id in st.session_state.chat_sessions:
        # Sauvegarder la session actuelle si elle contient des messages
        if st.session_state.chat_history:
            save_current_session()
        
        # Charger la session
        session_data = st.session_state.chat_sessions[session_id]
        st.session_state.chat_history = session_data['messages']
        st.session_state.current_session_id = session_id
        st.rerun()

def generate_session_id() -> str:
    """Génère un ID de session unique"""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Exemples de réponses prédéfinies pour démo
DEMO_RESPONSES = {
    "abus de biens sociaux": """L'abus de biens sociaux (ABS) est défini aux articles L. 241-3 (SARL) et L. 242-6 (SA) du Code de commerce.

**Éléments constitutifs :**
1. **Usage des biens ou du crédit** de la société
2. **Contraire à l'intérêt social**
3. **À des fins personnelles** ou pour favoriser une autre société
4. **Mauvaise foi** du dirigeant

**Jurisprudence constante :**
- Cass. crim., 27 octobre 2021, n° 20-86.531 : la mauvaise foi est caractérisée dès lors que le dirigeant savait que l'acte était contraire à l'intérêt social
- Cass. crim., 8 septembre 2021, n° 20-83.098 : l'intérêt du groupe ne justifie pas systématiquement l'usage des biens sociaux

**Sanctions :** 5 ans d'emprisonnement et 375 000 € d'amende.""",

    "corruption": """La corruption est réprimée par plusieurs articles du Code pénal selon les acteurs :

**Corruption active :**
- Article 433-1 CP : corruption d'agent public français
- Article 435-3 CP : corruption d'agent public étranger
- Article 445-1 CP : corruption privée

**Corruption passive :**
- Article 432-11 CP : pour les personnes dépositaires de l'autorité publique
- Article 435-1 CP : agents publics étrangers
- Article 445-2 CP : corruption privée

**Éléments essentiels :**
1. **Pacte de corruption** (accord préalable)
2. **Sollicitation ou agrément** d'offres ou promesses
3. **Contrepartie** : accomplir ou s'abstenir d'accomplir un acte
4. **Antériorité** du pacte par rapport à l'acte

**Jurisprudence :** Cass. crim., 16 décembre 2020, n° 18-86.855"""
}

# Point d'entrée
if __name__ == "__main__":
    show()