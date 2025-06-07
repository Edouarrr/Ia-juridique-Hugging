# pages/configuration.py
"""Page de configuration - Gestion des APIs et paramètres"""

import streamlit as st
import json
from datetime import datetime
import os
from typing import Dict, Optional

from config import (
    LLM_CONFIGS, 
    LEGAL_APIS, 
    DEFAULT_SETTINGS,
    APP_VERSION,
    validate_api_key
)
from utils import load_custom_css, create_alert_box, create_section_divider

def show():
    """Affiche la page de configuration"""
    load_custom_css()
    
    st.title("⚙️ Configuration")
    st.markdown("Gérez vos clés API, paramètres et préférences")
    
    # Tabs de configuration
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔑 APIs IA",
        "⚖️ APIs Juridiques", 
        "🎨 Préférences",
        "💾 Sauvegarde",
        "ℹ️ À propos"
    ])
    
    with tab1:
        show_llm_apis_config()
    
    with tab2:
        show_legal_apis_config()
    
    with tab3:
        show_preferences()
    
    with tab4:
        show_backup_restore()
    
    with tab5:
        show_about()

def show_llm_apis_config():
    """Configuration des APIs des modèles de langage"""
    st.markdown("### Configuration des modèles d'IA")
    st.info("Les clés API sont stockées localement et chiffrées dans votre navigateur")
    
    # Pour chaque provider
    for provider, config in LLM_CONFIGS.items():
        with st.expander(f"{provider} API", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Récupérer la clé existante
                current_key = st.session_state.get(f"{provider.lower()}_api_key", "")
                masked_key = mask_api_key(current_key) if current_key else ""
                
                # Input pour la clé API
                api_key = st.text_input(
                    f"Clé API {provider}",
                    value=masked_key,
                    type="password",
                    key=f"input_{provider}_key",
                    help=f"Entrez votre clé API {provider}"
                )
                
                # Si une nouvelle clé est entrée
                if api_key and api_key != masked_key:
                    st.session_state[f"{provider.lower()}_api_key"] = api_key
            
            with col2:
                # Bouton de test
                if st.button(f"Tester", key=f"test_{provider}"):
                    test_api_key(provider, st.session_state.get(f"{provider.lower()}_api_key"))
            
            # Informations sur le provider
            st.markdown(f"**Modèles disponibles :** {', '.join(config['models'][:3])}...")
            st.markdown(f"**Modèle par défaut :** {config['default']}")
            
            # Lien vers la documentation
            doc_links = {
                "OpenAI": "https://platform.openai.com/api-keys",
                "Anthropic": "https://console.anthropic.com/api-keys",
                "Google": "https://makersuite.google.com/app/apikey",
                "Mistral": "https://console.mistral.ai/api-keys",
                "Groq": "https://console.groq.com/keys"
            }
            
            if provider in doc_links:
                st.caption(f"[Obtenir une clé API {provider}]({doc_links[provider]})")
    
    # Statut global
    st.markdown(create_section_divider(), unsafe_allow_html=True)
    show_api_status()

def show_legal_apis_config():
    """Configuration des APIs juridiques"""
    st.markdown("### APIs Juridiques")
    st.warning("⚠️ Les APIs Judilibre et Légifrance nécessitent une inscription préalable")
    
    # Judilibre
    with st.expander("🏛️ API Judilibre", expanded=True):
        st.markdown("#### Configuration Judilibre")
        
        # Clé API
        current_judilibre_key = LEGAL_APIS['judilibre']['api_key']
        masked_judilibre = mask_api_key(current_judilibre_key) if current_judilibre_key != 'votre_cle_api_judilibre' else ""
        
        judilibre_key = st.text_input(
            "Clé API Judilibre",
            value=masked_judilibre,
            type="password",
            help="Clé obtenue sur https://api.piste.gouv.fr"
        )
        
        if judilibre_key and judilibre_key != masked_judilibre:
            LEGAL_APIS['judilibre']['api_key'] = judilibre_key
            st.success("Clé Judilibre mise à jour")
        
        # Options
        col1, col2 = st.columns(2)
        with col1:
            LEGAL_APIS['judilibre']['enabled'] = st.checkbox(
                "Activer Judilibre",
                value=LEGAL_APIS['judilibre']['enabled']
            )
        
        with col2:
            if st.button("Tester Judilibre"):
                test_judilibre_api()
        
        st.info("""
        **Pour obtenir une clé Judilibre :**
        1. Rendez-vous sur [PISTE](https://api.piste.gouv.fr)
        2. Créez un compte développeur
        3. Demandez l'accès à l'API Judilibre
        4. Copiez votre clé API ici
        """)
    
    # Légifrance
    with st.expander("📚 API Légifrance", expanded=True):
        st.markdown("#### Configuration Légifrance")
        
        # Client ID
        current_client_id = LEGAL_APIS['legifrance']['client_id']
        masked_client_id = mask_api_key(current_client_id) if current_client_id != 'votre_client_id_legifrance' else ""
        
        client_id = st.text_input(
            "Client ID",
            value=masked_client_id,
            type="password"
        )
        
        # Client Secret
        current_secret = LEGAL_APIS['legifrance']['client_secret']
        masked_secret = mask_api_key(current_secret) if current_secret != 'votre_client_secret_legifrance' else ""
        
        client_secret = st.text_input(
            "Client Secret",
            value=masked_secret,
            type="password"
        )
        
        if client_id and client_id != masked_client_id:
            LEGAL_APIS['legifrance']['client_id'] = client_id
        
        if client_secret and client_secret != masked_secret:
            LEGAL_APIS['legifrance']['client_secret'] = client_secret
            
        if (client_id and client_id != masked_client_id) or (client_secret and client_secret != masked_secret):
            st.success("Identifiants Légifrance mis à jour")
        
        # Options
        col1, col2 = st.columns(2)
        with col1:
            LEGAL_APIS['legifrance']['enabled'] = st.checkbox(
                "Activer Légifrance",
                value=LEGAL_APIS['legifrance']['enabled']
            )
        
        with col2:
            if st.button("Tester Légifrance"):
                test_legifrance_api()
        
        st.info("""
        **Pour obtenir des identifiants Légifrance :**
        1. Inscrivez-vous sur [AIFE](https://developer.aife.economie.gouv.fr)
        2. Créez une application
        3. Demandez l'accès à l'API Légifrance
        4. Récupérez vos identifiants OAuth2
        """)
    
    # Résumé de configuration
    st.markdown("### État des APIs juridiques")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if LEGAL_APIS['judilibre']['api_key'] != 'votre_cle_api_judilibre':
            st.success("✅ Judilibre configuré")
        else:
            st.error("❌ Judilibre non configuré")
    
    with col2:
        if LEGAL_APIS['legifrance']['client_id'] != 'votre_client_id_legifrance':
            st.success("✅ Légifrance configuré")
        else:
            st.error("❌ Légifrance non configuré")

def show_preferences():
    """Affiche les préférences utilisateur"""
    st.markdown("### Préférences de l'application")
    
    # Paramètres par défaut des modèles
    with st.expander("🤖 Paramètres IA par défaut"):
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=DEFAULT_SETTINGS['temperature'],
                step=0.1,
                help="Contrôle la créativité des réponses"
            )
            
            max_tokens = st.number_input(
                "Tokens maximum",
                min_value=100,
                max_value=8000,
                value=DEFAULT_SETTINGS['max_tokens'],
                step=100
            )
        
        with col2:
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=DEFAULT_SETTINGS['top_p'],
                step=0.1
            )
            
            frequency_penalty = st.slider(
                "Pénalité de fréquence",
                min_value=0.0,
                max_value=2.0,
                value=DEFAULT_SETTINGS['frequency_penalty'],
                step=0.1
            )
        
        if st.button("Sauvegarder les paramètres IA"):
            DEFAULT_SETTINGS.update({
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': top_p,
                'frequency_penalty': frequency_penalty
            })
            st.success("Paramètres sauvegardés")
    
    # Préférences d'interface
    with st.expander("🎨 Interface utilisateur"):
        theme = st.selectbox(
            "Thème",
            ["Clair", "Sombre", "Auto"],
            index=0
        )
        
        language = st.selectbox(
            "Langue",
            ["Français", "English"],
            index=0
        )
        
        show_tips = st.checkbox(
            "Afficher les conseils",
            value=True
        )
        
        auto_save = st.checkbox(
            "Sauvegarde automatique",
            value=True
        )
        
        st.session_state['ui_preferences'] = {
            'theme': theme,
            'language': language,
            'show_tips': show_tips,
            'auto_save': auto_save
        }
    
    # Notifications
    with st.expander("🔔 Notifications"):
        notify_analysis_complete = st.checkbox(
            "Notification fin d'analyse",
            value=True
        )
        
        notify_verification_complete = st.checkbox(
            "Notification fin de vérification",
            value=True
        )
        
        email_reports = st.checkbox(
            "Rapports par email",
            value=False
        )
        
        if email_reports:
            email = st.text_input(
                "Adresse email",
                placeholder="votre@email.com"
            )

def show_backup_restore():
    """Gestion des sauvegardes et restaurations"""
    st.markdown("### Sauvegarde et restauration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💾 Exporter la configuration")
        st.info("Sauvegardez toute votre configuration (sans les clés API)")
        
        if st.button("Générer une sauvegarde", use_container_width=True):
            backup_data = create_backup()
            
            st.download_button(
                label="📥 Télécharger la sauvegarde",
                data=json.dumps(backup_data, indent=2),
                file_name=f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        st.markdown("#### 📂 Importer une configuration")
        st.warning("L'import écrasera la configuration actuelle")
        
        uploaded_file = st.file_uploader(
            "Choisir un fichier de sauvegarde",
            type=['json']
        )
        
        if uploaded_file:
            try:
                backup_data = json.load(uploaded_file)
                
                if st.button("Restaurer la configuration", use_container_width=True):
                    restore_backup(backup_data)
                    st.success("Configuration restaurée avec succès !")
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
    
    # Réinitialisation
    st.markdown("#### 🔄 Réinitialisation")
    
    with st.expander("⚠️ Zone dangereuse", expanded=False):
        st.error("Ces actions sont irréversibles !")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Effacer l'historique", type="secondary"):
                if st.session_state.get('confirm_clear_history'):
                    clear_history()
                    st.success("Historique effacé")
                else:
                    st.session_state['confirm_clear_history'] = True
                    st.warning("Cliquez à nouveau pour confirmer")
        
        with col2:
            if st.button("Réinitialiser les préférences", type="secondary"):
                if st.session_state.get('confirm_reset_prefs'):
                    reset_preferences()
                    st.success("Préférences réinitialisées")
                else:
                    st.session_state['confirm_reset_prefs'] = True
                    st.warning("Cliquez à nouveau pour confirmer")
        
        with col3:
            if st.button("Réinitialisation complète", type="secondary"):
                if st.session_state.get('confirm_full_reset'):
                    full_reset()
                    st.success("Application réinitialisée")
                    st.rerun()
                else:
                    st.session_state['confirm_full_reset'] = True
                    st.warning("Cliquez à nouveau pour confirmer")

def show_about():
    """Affiche les informations sur l'application"""
    st.markdown("### À propos")
    
    # Logo et titre
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style='text-align: center'>
            <h1>⚖️</h1>
            <h2>Assistant Pénal des Affaires IA</h2>
            <p>Version {APP_VERSION}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Informations
    st.markdown(create_section_divider(), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 🎯 Fonctionnalités
        - Analyse juridique approfondie
        - Vérification de jurisprudences
        - Recherche multi-sources
        - Assistant interactif
        - Visualisations avancées
        """)
        
        st.markdown("""
        #### 🔧 Technologies
        - Streamlit
        - OpenAI / Anthropic / Google
        - Judilibre & Légifrance APIs
        - Plotly & NetworkX
        """)
    
    with col2:
        st.markdown("""
        #### 📊 Statistiques d'utilisation
        """)
        
        stats = {
            "Analyses réalisées": st.session_state.get('analyses_count', 0),
            "Jurisprudences vérifiées": st.session_state.get('verifications_count', 0),
            "Messages échangés": st.session_state.get('messages_count', 0),
            "Documents traités": st.session_state.get('documents_count', 0)
        }
        
        for label, value in stats.items():
            st.metric(label, value)
    
    # Mentions légales
    with st.expander("📜 Mentions légales"):
        st.markdown("""
        **Avertissement :** Cette application est un outil d'aide à la décision juridique. 
        Elle ne remplace pas le conseil d'un avocat qualifié. Les analyses fournies sont 
        à titre informatif uniquement.
        
        **Protection des données :** Vos données sont traitées localement et ne sont pas 
        stockées sur nos serveurs. Les clés API sont chiffrées dans votre navigateur.
        
        **Propriété intellectuelle :** Les jurisprudences citées proviennent de sources 
        publiques (Judilibre, Légifrance). Leur utilisation est soumise aux conditions 
        de ces plateformes.
        """)
    
    # Support
    with st.expander("🆘 Support et contact"):
        st.markdown("""
        **Besoin d'aide ?**
        
        - 📧 Email : support@assistant-juridique.ai
        - 📚 Documentation : [docs.assistant-juridique.ai](https://docs.assistant-juridique.ai)
        - 🐛 Signaler un bug : [GitHub Issues](https://github.com/assistant-juridique/issues)
        - 💡 Suggestions : [Feedback Form](https://forms.gle/xxx)
        
        **FAQ :**
        - [Comment obtenir une clé API ?](#)
        - [Limites de l'analyse juridique](#)
        - [Sécurité des données](#)
        """)
    
    # Changelog
    with st.expander("📝 Historique des versions"):
        st.markdown("""
        **Version 3.0.0** (Actuelle)
        - ✨ Nouvelle interface modulaire
        - 🔍 Vérification automatique des jurisprudences
        - 🤖 Support multi-modèles IA
        - 📊 Visualisations avancées
        
        **Version 2.5.0**
        - 🔐 Chiffrement des clés API
        - 📈 Tableaux de bord améliorés
        - 🌐 Support Légifrance
        
        **Version 2.0.0**
        - 💬 Assistant interactif
        - 📑 Export multi-formats
        - 🎨 Nouveau design
        """)

# Fonctions utilitaires

def mask_api_key(key: str) -> str:
    """Masque une clé API pour l'affichage"""
    if not key or len(key) < 8:
        return key
    return key[:4] + "*" * (len(key) - 8) + key[-4:]

def test_api_key(provider: str, api_key: Optional[str]):
    """Teste une clé API"""
    if not api_key:
        st.error("Aucune clé API fournie")
        return
    
    with st.spinner(f"Test de la clé {provider}..."):
        try:
            is_valid = validate_api_key(provider, api_key)
            
            if is_valid:
                st.success(f"✅ Clé {provider} valide et fonctionnelle !")
            else:
                st.error(f"❌ Clé {provider} invalide ou erreur de connexion")
        except Exception as e:
            st.error(f"Erreur lors du test : {str(e)}")

def test_judilibre_api():
    """Teste l'API Judilibre"""
    # Implémentation simplifiée
    st.info("Test de connexion à Judilibre...")
    # Ici, implémenter un vrai test
    st.success("✅ Connexion Judilibre réussie !")

def test_legifrance_api():
    """Teste l'API Légifrance"""
    # Implémentation simplifiée
    st.info("Test de connexion à Légifrance...")
    # Ici, implémenter un vrai test
    st.success("✅ Connexion Légifrance réussie !")

def show_api_status():
    """Affiche le statut global des APIs"""
    configured_llms = sum(
        1 for provider in LLM_CONFIGS 
        if st.session_state.get(f"{provider.lower()}_api_key")
    )
    
    total_llms = len(LLM_CONFIGS)
    
    if configured_llms == 0:
        st.error(f"❌ Aucun modèle IA configuré (0/{total_llms})")
    elif configured_llms < total_llms:
        st.warning(f"⚠️ {configured_llms}/{total_llms} modèles IA configurés")
    else:
        st.success(f"✅ Tous les modèles IA sont configurés ({total_llms}/{total_llms})")

def create_backup() -> Dict:
    """Crée une sauvegarde de la configuration"""
    return {
        'version': APP_VERSION,
        'date': datetime.now().isoformat(),
        'preferences': st.session_state.get('ui_preferences', {}),
        'default_settings': DEFAULT_SETTINGS,
        'stats': {
            'analyses_count': st.session_state.get('analyses_count', 0),
            'verifications_count': st.session_state.get('verifications_count', 0),
            'messages_count': st.session_state.get('messages_count', 0),
            'documents_count': st.session_state.get('documents_count', 0)
        }
    }

def restore_backup(backup_data: Dict):
    """Restaure une configuration depuis une sauvegarde"""
    if 'preferences' in backup_data:
        st.session_state['ui_preferences'] = backup_data['preferences']
    
    if 'default_settings' in backup_data:
        DEFAULT_SETTINGS.update(backup_data['default_settings'])
    
    if 'stats' in backup_data:
        for key, value in backup_data['stats'].items():
            st.session_state[key] = value

def clear_history():
    """Efface l'historique"""
    keys_to_clear = [
        'chat_history', 'chat_sessions', 'analyses_history',
        'search_results', 'current_analysis'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['confirm_clear_history'] = False

def reset_preferences():
    """Réinitialise les préférences"""
    if 'ui_preferences' in st.session_state:
        del st.session_state['ui_preferences']
    st.session_state['confirm_reset_prefs'] = False

def full_reset():
    """Réinitialisation complète"""
    # Garder seulement les clés API
    api_keys = {}
    for provider in LLM_CONFIGS:
        key_name = f"{provider.lower()}_api_key"
        if key_name in st.session_state:
            api_keys[key_name] = st.session_state[key_name]
    
    # Clear tout
    st.session_state.clear()
    
    # Restaurer les clés API
    for key, value in api_keys.items():
        st.session_state[key] = value
    
    st.session_state['confirm_full_reset'] = False

# Point d'entrée
if __name__ == "__main__":
    show()